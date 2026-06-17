import React, {useEffect, useMemo, useState} from 'react';
import styles from './styles.module.css';

type CacheMode = 'slurm' | 'deps';

type CacheObject = {
  key: string;
  lastModified: string;
  size: number;
};

type PackageEntry = CacheObject & {
  id: string;
  name: string;
  fileName: string;
  mirrorPath: string;
  manifestUrl: string;
};

type ManifestLayer = {
  contentLength: number;
  mediaType: string;
  compression?: string;
  checksumAlgorithm?: string;
  checksum: string;
};

type SignedManifest = {
  version: number;
  data: ManifestLayer[];
};

type SpecNode = {
  name?: string;
  version?: string;
  namespace?: string;
  hash?: string;
  package_hash?: string;
  arch?: {
    platform?: string;
    platform_os?: string;
    target?: string;
  };
  compiler?: {
    name?: string;
    version?: string;
  };
  parameters?: Record<string, unknown>;
  dependencies?: Array<{
    name?: string;
    hash?: string;
    parameters?: {
      deptypes?: string[];
      virtuals?: string[];
    };
  }>;
};

type SpecDocument = {
  spec?: {
    nodes?: SpecNode[];
  };
  buildcache_layout_version?: number;
};

type DetailState = {
  status: 'idle' | 'loading' | 'loaded' | 'error';
  error?: string;
  manifest?: SignedManifest;
  spec?: SpecDocument;
  rawManifest?: string;
};

const BASE_URL = 'https://slurm-factory-spack-binary-cache.vantagecompute.ai';
const TOOLCHAINS = ['resolute', 'noble', 'jammy', 'rockylinux10', 'rockylinux9', 'rockylinux8'];
const SLURM_VERSIONS = ['26.05', '25.11', '24.11', '23.11'];
const PAGE_SIZE = 1000;

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return 'unknown';
  }

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  for (const unit of units) {
    if (size < 1024 || unit === units[units.length - 1]) {
      return unit === 'B' ? `${Math.round(size)} ${unit}` : `${size.toFixed(1)} ${unit}`;
    }
    size /= 1024;
  }

  return `${bytes} B`;
}

function formatDate(value: string): string {
  if (!value) {
    return 'unknown';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function mirrorPathFor(mode: CacheMode, toolchain: string, slurmVersion: string): string {
  if (mode === 'deps') {
    return `${toolchain}/slurm/deps/`;
  }

  return `${toolchain}/slurm/${slurmVersion}/`;
}

function packagePrefixFor(mode: CacheMode, toolchain: string, slurmVersion: string): string {
  return `${mirrorPathFor(mode, toolchain, slurmVersion)}v3/manifests/spec/`;
}

function objectUrl(key: string): string {
  return `${BASE_URL}/${key.split('/').map(encodeURIComponent).join('/')}`;
}

function parseS3List(xmlText: string): {objects: CacheObject[]; nextToken: string | null} {
  const document = new DOMParser().parseFromString(xmlText, 'application/xml');
  const error = document.querySelector('parsererror');
  if (error) {
    throw new Error('The cache listing response was not valid XML.');
  }

  const contents = Array.from(document.getElementsByTagName('Contents'));
  const objects = contents.map((node) => ({
    key: node.getElementsByTagName('Key')[0]?.textContent ?? '',
    lastModified: node.getElementsByTagName('LastModified')[0]?.textContent ?? '',
    size: Number(node.getElementsByTagName('Size')[0]?.textContent ?? 0),
  })).filter((object) => object.key.length > 0);

  return {
    objects,
    nextToken: document.getElementsByTagName('NextContinuationToken')[0]?.textContent ?? null,
  };
}

async function fetchListing(prefix: string, signal: AbortSignal): Promise<CacheObject[]> {
  let nextToken: string | null = null;
  const objects: CacheObject[] = [];

  do {
    const params = new URLSearchParams({
      'list-type': '2',
      prefix,
      'max-keys': String(PAGE_SIZE),
    });

    if (nextToken) {
      params.set('continuation-token', nextToken);
    }

    const response = await fetch(`${BASE_URL}/?${params.toString()}`, {signal});
    if (!response.ok) {
      throw new Error(`Cache listing failed with HTTP ${response.status}.`);
    }

    const page = parseS3List(await response.text());
    objects.push(...page.objects);
    nextToken = page.nextToken;
  } while (nextToken);

  return objects;
}

function packageEntryFromObject(object: CacheObject, mirrorPath: string): PackageEntry | null {
  if (!object.key.endsWith('.spec.manifest.json')) {
    return null;
  }

  const relativeKey = object.key.slice(`${mirrorPath}v3/manifests/spec/`.length);
  const parts = relativeKey.split('/');
  if (parts.length !== 2) {
    return null;
  }

  return {
    ...object,
    id: object.key,
    name: parts[0],
    fileName: parts[1],
    mirrorPath,
    manifestUrl: objectUrl(object.key),
  };
}

function extractSignedJson(text: string): string {
  const messageStart = '-----BEGIN PGP SIGNED MESSAGE-----';
  const signatureStart = '-----BEGIN PGP SIGNATURE-----';

  if (!text.includes(messageStart)) {
    return text.trim();
  }

  const bodyStart = text.indexOf('\n\n');
  const signatureIndex = text.indexOf(signatureStart);
  if (bodyStart === -1 || signatureIndex === -1) {
    throw new Error('The signed manifest did not contain a parseable JSON body.');
  }

  return text.slice(bodyStart + 2, signatureIndex).trim();
}

async function gunzipJson<T>(buffer: ArrayBuffer): Promise<T> {
  if (!('DecompressionStream' in window)) {
    throw new Error('This browser cannot decompress Spack spec blobs. Try a recent Chrome, Edge, Firefox, or Safari.');
  }

  const stream = new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Response(stream).json() as Promise<T>;
}

function findSpecLayer(manifest: SignedManifest): ManifestLayer | undefined {
  return manifest.data.find((layer) => layer.mediaType.includes('spec'));
}

function blobUrl(entry: PackageEntry, layer: ManifestLayer): string {
  return `${BASE_URL}/${entry.mirrorPath}blobs/sha256/${layer.checksum.slice(0, 2)}/${layer.checksum}`;
}

function primaryNode(spec?: SpecDocument): SpecNode | undefined {
  return spec?.spec?.nodes?.[0];
}

function PackageDetails({entry}: {entry: PackageEntry}) {
  const [detail, setDetail] = useState<DetailState>({status: 'idle'});

  useEffect(() => {
    const controller = new AbortController();

    async function loadDetails() {
      setDetail({status: 'loading'});
      try {
        const manifestResponse = await fetch(entry.manifestUrl, {signal: controller.signal});
        if (!manifestResponse.ok) {
          throw new Error(`Manifest fetch failed with HTTP ${manifestResponse.status}.`);
        }

        const rawManifest = await manifestResponse.text();
        const manifest = JSON.parse(extractSignedJson(rawManifest)) as SignedManifest;
        const specLayer = findSpecLayer(manifest);
        let spec: SpecDocument | undefined;

        if (specLayer) {
          const specResponse = await fetch(blobUrl(entry, specLayer), {signal: controller.signal});
          if (!specResponse.ok) {
            throw new Error(`Spec blob fetch failed with HTTP ${specResponse.status}.`);
          }
          spec = await gunzipJson<SpecDocument>(await specResponse.arrayBuffer());
        }

        setDetail({status: 'loaded', manifest, spec, rawManifest: extractSignedJson(rawManifest)});
      } catch (error) {
        if (!controller.signal.aborted) {
          setDetail({status: 'error', error: error instanceof Error ? error.message : String(error)});
        }
      }
    }

    loadDetails();
    return () => controller.abort();
  }, [entry]);

  const node = primaryNode(detail.spec);
  const dependencies = node?.dependencies ?? [];

  return (
    <aside className={styles.details} aria-live="polite">
      <div className={styles.detailsHeader}>
        <div>
          <h3>{node?.name ?? entry.name}</h3>
          <p>{node?.version ?? entry.fileName.replace('.spec.manifest.json', '')}</p>
        </div>
        <a href={entry.manifestUrl} target="_blank" rel="noreferrer">Manifest</a>
      </div>

      {detail.status === 'loading' && <p className={styles.muted}>Loading package details...</p>}
      {detail.status === 'error' && <p className={styles.error}>{detail.error}</p>}

      {detail.status === 'loaded' && (
        <>
          <dl className={styles.detailGrid}>
            <div><dt>Version</dt><dd>{node?.version ?? 'unknown'}</dd></div>
            <div><dt>Platform</dt><dd>{node?.arch?.platform_os ?? node?.arch?.platform ?? 'unknown'}</dd></div>
            <div><dt>Target</dt><dd>{node?.arch?.target ?? 'unknown'}</dd></div>
            <div><dt>Compiler</dt><dd>{node?.compiler ? `${node.compiler.name}@${node.compiler.version}` : 'unknown'}</dd></div>
            <div><dt>Namespace</dt><dd>{node?.namespace ?? 'unknown'}</dd></div>
            <div><dt>Spec hash</dt><dd>{node?.hash ?? node?.package_hash ?? 'unknown'}</dd></div>
            <div><dt>Manifest size</dt><dd>{formatBytes(entry.size)}</dd></div>
            <div><dt>Last modified</dt><dd>{formatDate(entry.lastModified)}</dd></div>
          </dl>

          <h4>Buildcache Layers</h4>
          <div className={styles.layers}>
            {detail.manifest?.data.map((layer) => (
              <div className={styles.layer} key={`${layer.mediaType}-${layer.checksum}`}>
                <strong>{layer.mediaType}</strong>
                <span>{formatBytes(layer.contentLength)}</span>
                <code>{layer.checksumAlgorithm ?? 'checksum'}:{layer.checksum}</code>
                <a href={blobUrl(entry, layer)} target="_blank" rel="noreferrer">Blob</a>
              </div>
            ))}
          </div>

          <h4>Variants and Parameters</h4>
          <pre className={styles.pre}>{JSON.stringify(node?.parameters ?? {}, null, 2)}</pre>

          <h4>Dependencies ({dependencies.length})</h4>
          <div className={styles.dependencies}>
            {dependencies.map((dependency) => (
              <div className={styles.dependency} key={`${dependency.name}-${dependency.hash}`}>
                <strong>{dependency.name}</strong>
                <code>{dependency.hash}</code>
                <span>{dependency.parameters?.deptypes?.join(', ') || 'dependency'}</span>
              </div>
            ))}
          </div>

          <details className={styles.rawDetails}>
            <summary>Raw Spack spec JSON</summary>
            <pre className={styles.pre}>{JSON.stringify(detail.spec, null, 2)}</pre>
          </details>
        </>
      )}
    </aside>
  );
}

export default function SpackCacheBrowser() {
  const [toolchain, setToolchain] = useState('noble');
  const [slurmVersion, setSlurmVersion] = useState('25.11');
  const [mode, setMode] = useState<CacheMode>('slurm');
  const [query, setQuery] = useState('');
  const [entries, setEntries] = useState<PackageEntry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'loaded' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  const mirrorPath = useMemo(() => mirrorPathFor(mode, toolchain, slurmVersion), [mode, toolchain, slurmVersion]);
  const prefix = useMemo(() => packagePrefixFor(mode, toolchain, slurmVersion), [mode, toolchain, slurmVersion]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPackages() {
      setStatus('loading');
      setError(null);
      setEntries([]);
      setSelectedId(null);

      try {
        const objects = await fetchListing(prefix, controller.signal);
        if (controller.signal.aborted) {
          return;
        }

        const packages = objects
          .map((object) => packageEntryFromObject(object, mirrorPath))
          .filter((entry): entry is PackageEntry => Boolean(entry))
          .sort((left, right) => left.name.localeCompare(right.name) || left.fileName.localeCompare(right.fileName));

        setEntries(packages);
        setSelectedId(packages[0]?.id ?? null);
        setStatus('loaded');
      } catch (error) {
        if (!controller.signal.aborted) {
          setStatus('error');
          setError(error instanceof Error ? error.message : String(error));
        }
      }
    }

    loadPackages();
    return () => controller.abort();
  }, [prefix, mirrorPath]);

  const filteredEntries = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) {
      return entries;
    }

    return entries.filter((entry) => (
      entry.name.toLowerCase().includes(normalizedQuery)
      || entry.fileName.toLowerCase().includes(normalizedQuery)
      || entry.key.toLowerCase().includes(normalizedQuery)
    ));
  }, [entries, query]);

  const selectedEntry = filteredEntries.find((entry) => entry.id === selectedId) ?? filteredEntries[0] ?? null;

  return (
    <section className={styles.browser}>
      <div className={styles.header}>
        <div>
          <h2>Live Spack Cache Browser</h2>
          <p>Fetched in your browser from the public CloudFront-backed Spack cache.</p>
        </div>
        <a className={styles.cacheLink} href={`${BASE_URL}/${mirrorPath}`} target="_blank" rel="noreferrer">
          Open mirror
        </a>
      </div>

      <div className={styles.controls}>
        <label>
          Cache
          <select value={mode} onChange={(event) => setMode(event.target.value as CacheMode)}>
            <option value="slurm">Slurm packages</option>
            <option value="deps">Dependencies</option>
          </select>
        </label>
        <label>
          Toolchain
          <select value={toolchain} onChange={(event) => setToolchain(event.target.value)}>
            {TOOLCHAINS.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Slurm version
          <select value={slurmVersion} onChange={(event) => setSlurmVersion(event.target.value)} disabled={mode === 'deps'}>
            {SLURM_VERSIONS.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label className={styles.search}>
          Filter packages
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="slurm, cuda, openmpi..." />
        </label>
      </div>

      <div className={styles.summaryBar}>
        <span><strong>{filteredEntries.length}</strong> shown</span>
        <span><strong>{entries.length}</strong> in mirror</span>
        <code>{prefix}</code>
      </div>

      {status === 'loading' && <p className={styles.muted}>Loading package manifests from the cache...</p>}
      {status === 'error' && <p className={styles.error}>{error}</p>}
      {status === 'loaded' && entries.length === 0 && (
        <p className={styles.muted}>No package manifests were found for this cache selection.</p>
      )}
      {status === 'loaded' && entries.length > 0 && filteredEntries.length === 0 && (
        <p className={styles.muted}>No packages match the current filter.</p>
      )}

      {status === 'loaded' && filteredEntries.length > 0 && (
        <div className={styles.content}>
          <div className={styles.packageList} role="list" aria-label="Spack packages">
            {filteredEntries.map((entry) => (
              <button
                className={entry.id === selectedEntry?.id ? styles.packageButtonActive : styles.packageButton}
                key={entry.id}
                onClick={() => setSelectedId(entry.id)}
                type="button"
              >
                <span>{entry.name}</span>
                <small>{entry.fileName}</small>
                <small>{formatBytes(entry.size)} · {formatDate(entry.lastModified)}</small>
              </button>
            ))}
          </div>
          {selectedEntry && <PackageDetails entry={selectedEntry} key={selectedEntry.id} />}
        </div>
      )}
    </section>
  );
}

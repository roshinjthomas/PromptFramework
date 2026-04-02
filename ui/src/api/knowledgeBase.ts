/**
 * Knowledge Base API.
 * GET    /api/kb
 * POST   /api/kb/ingest
 * DELETE /api/kb/:doc_id
 */

export interface KBDocument {
  source_file: string
  chunk_count: number
}

export interface IngestResponse {
  source_file: string
  pages_parsed: number
  chunks_created: number
  embed_time_s: number
  ingest_time_s: number
  total_chunks_in_store: number
  label: string
  status: string
}

export interface DeleteResponse {
  source_file: string
  chunks_deleted: number
  message: string
}

const BASE_URL = '/api/kb'

export async function fetchKBDocuments(): Promise<KBDocument[]> {
  const response = await fetch(BASE_URL)
  if (!response.ok) {
    throw new Error(`Failed to fetch KB documents (${response.status})`)
  }
  return response.json()
}

export async function ingestDocument(
  file: File,
  label?: string,
  replace = false,
): Promise<IngestResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (label) formData.append('label', label)
  formData.append('replace', String(replace))

  const response = await fetch(`${BASE_URL}/ingest`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const err = await response.text()
    throw new Error(`Ingestion failed (${response.status}): ${err}`)
  }

  return response.json()
}

export async function removeDocument(docId: string): Promise<DeleteResponse> {
  const response = await fetch(`${BASE_URL}/${encodeURIComponent(docId)}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    const err = await response.text()
    throw new Error(`Failed to remove document (${response.status}): ${err}`)
  }

  return response.json()
}

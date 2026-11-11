export interface ApiError {
  code: string
  message: string
  detail?: unknown
  request_id?: string | null
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

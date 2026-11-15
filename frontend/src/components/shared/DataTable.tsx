import { AlertCircle, ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Inbox, Search } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { EmptyState } from '@/components/shared/EmptyState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

type SortValue = string | number | boolean | null | undefined

export interface DataTableColumn<T> {
  id: string
  header: ReactNode
  cell: (row: T) => ReactNode
  /** Provide to make the column sortable (sorts the rows currently loaded). */
  sortValue?: (row: T) => SortValue
  className?: string
  headerClassName?: string
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  getRowId: (row: T) => string | number
  caption: string
  isLoading?: boolean
  isFetching?: boolean
  error?: string | null
  onRetry?: () => void
  /** Server-driven search: `onChange` fires 350 ms after the user stops typing. */
  search?: { value: string; onChange: (value: string) => void; placeholder?: string }
  /** Extra filter controls rendered next to the search box. */
  filters?: ReactNode
  /** Server-driven pagination (1-based page). Omit to show every row. */
  pagination?: {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
    onPageSizeChange?: (size: number) => void
    pageSizeOptions?: number[]
  }
  emptyTitle?: string
  emptyDescription?: string
}

function compare(a: SortValue, b: SortValue): number {
  if (a == null && b == null) return 0
  if (a == null) return 1 // empty values always last
  if (b == null) return -1
  if (typeof a === 'string' && typeof b === 'string') return a.localeCompare(b, undefined, { sensitivity: 'base' })
  return a < b ? -1 : a > b ? 1 : 0
}

export function DataTable<T>({
  columns,
  data,
  getRowId,
  caption,
  isLoading = false,
  isFetching = false,
  error,
  onRetry,
  search,
  filters,
  pagination,
  emptyTitle = 'Nothing here yet',
  emptyDescription,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<{ id: string; dir: 'asc' | 'desc' } | null>(null)
  const [searchText, setSearchText] = useState(search?.value ?? '')
  const debounce = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(debounce.current), [])

  const rows = useMemo(() => {
    const column = sort ? columns.find((c) => c.id === sort.id) : undefined
    if (!sort || !column?.sortValue) return data
    const getValue = column.sortValue
    const factor = sort.dir === 'asc' ? 1 : -1
    return [...data].sort((a, b) => factor * compare(getValue(a), getValue(b)))
  }, [data, columns, sort])

  function toggleSort(id: string) {
    setSort((current) => {
      if (current?.id !== id) return { id, dir: 'asc' }
      if (current.dir === 'asc') return { id, dir: 'desc' }
      return null
    })
  }

  function onSearchInput(value: string) {
    setSearchText(value)
    window.clearTimeout(debounce.current)
    debounce.current = window.setTimeout(() => search?.onChange(value.trim()), 350)
  }

  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) : 1
  const from = pagination && pagination.total > 0 ? (pagination.page - 1) * pagination.pageSize + 1 : 0
  const to = pagination ? Math.min(pagination.page * pagination.pageSize, pagination.total) : rows.length
  const hasSortable = columns.some((c) => c.sortValue)
  const showSortNote = hasSortable && pagination !== undefined && pagination.total > data.length

  return (
    <div className="overflow-hidden rounded-lg border bg-card shadow-card">
      {(search || filters) && (
        <div className="flex flex-wrap items-center gap-3 border-b p-3 sm:p-4">
          {search && (
            <div className="relative min-w-[220px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
              <Input
                type="search"
                value={searchText}
                onChange={(event) => onSearchInput(event.target.value)}
                placeholder={search.placeholder ?? 'Search…'}
                aria-label={search.placeholder ?? 'Search'}
                className="pl-9"
              />
            </div>
          )}
          {filters}
        </div>
      )}

      <div className={cn('transition-opacity', isFetching && !isLoading && 'opacity-60')} aria-busy={isFetching}>
        {error ? (
          <EmptyState
            icon={AlertCircle}
            title="Could not load data"
            description={error}
            action={onRetry && <Button variant="outline" onClick={onRetry}>Try again</Button>}
          />
        ) : (
          <Table>
            <caption className="sr-only">{caption}</caption>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                {columns.map((column) => {
                  const active = sort?.id === column.id
                  const SortIcon = !active ? ArrowUpDown : sort.dir === 'asc' ? ArrowUp : ArrowDown
                  return (
                    <TableHead
                      key={column.id}
                      className={column.headerClassName}
                      aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                    >
                      {column.sortValue ? (
                        <button
                          type="button"
                          onClick={() => toggleSort(column.id)}
                          className="-ml-1 inline-flex items-center gap-1 rounded px-1 py-0.5 uppercase hover:text-foreground"
                        >
                          {column.header}
                          <SortIcon className={cn('size-3.5', active ? 'text-primary' : 'opacity-50')} aria-hidden />
                        </button>
                      ) : (
                        column.header
                      )}
                    </TableHead>
                  )
                })}
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 6 }).map((_, index) => (
                  <TableRow key={index} className="hover:bg-transparent">
                    {columns.map((column) => (
                      <TableCell key={column.id}>
                        <Skeleton className="h-5 w-full max-w-[160px]" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : rows.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={columns.length}>
                    <EmptyState icon={Inbox} title={emptyTitle} description={emptyDescription} />
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((row) => (
                  <TableRow key={getRowId(row)}>
                    {columns.map((column) => (
                      <TableCell key={column.id} className={column.className}>
                        {column.cell(row)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>

      {pagination && !error && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3 text-sm">
          <p className="text-muted-foreground" aria-live="polite">
            {pagination.total === 0 ? 'No results' : `Showing ${from}–${to} of ${pagination.total}`}
            {showSortNote && <span className="ml-2 text-xs">(sorting applies to this page)</span>}
          </p>
          <div className="flex items-center gap-3">
            {pagination.onPageSizeChange && (
              <label className="flex items-center gap-2 text-muted-foreground">
                <span className="hidden sm:inline">Rows</span>
                <Select
                  value={pagination.pageSize}
                  onChange={(event) => pagination.onPageSizeChange?.(Number(event.target.value))}
                  className="h-8 w-[76px] text-xs"
                  aria-label="Rows per page"
                >
                  {(pagination.pageSizeOptions ?? [10, 20, 50, 100]).map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </Select>
              </label>
            )}
            <nav className="flex items-center gap-1" aria-label="Pagination">
              <Button
                variant="outline"
                size="sm"
                onClick={() => pagination.onPageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
              >
                <ChevronLeft aria-hidden />
                <span className="sr-only sm:not-sr-only">Prev</span>
              </Button>
              <span className="min-w-[84px] px-2 text-center text-muted-foreground">
                Page {pagination.page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => pagination.onPageChange(pagination.page + 1)}
                disabled={pagination.page >= totalPages}
              >
                <span className="sr-only sm:not-sr-only">Next</span>
                <ChevronRight aria-hidden />
              </Button>
            </nav>
          </div>
        </div>
      )}
    </div>
  )
}

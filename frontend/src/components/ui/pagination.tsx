import { Button } from "@/components/ui/button";
import type { PageSize } from "@/hooks/usePageSize";

type PaginationProps = {
  page: number;
  pageSize: PageSize;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: PageSize) => void;
};

const PAGE_SIZE_OPTIONS: Array<{ value: PageSize; label: string }> = [
  { value: 25, label: "25" },
  { value: 50, label: "50" },
  { value: null, label: "All" },
];

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const effectivePageSize = pageSize ?? Math.max(total, 1);
  const totalPages = pageSize === null ? 1 : Math.max(1, Math.ceil(total / effectivePageSize));
  const boundedPage = Math.max(1, Math.min(page, totalPages));
  const start = total === 0 ? 0 : (boundedPage - 1) * effectivePageSize + 1;
  const end = total === 0 ? 0 : Math.min(total, boundedPage * effectivePageSize);
  const isPrevDisabled = boundedPage <= 1;
  const isNextDisabled = boundedPage >= totalPages;

  return (
    <div className="mt-4 flex flex-col gap-3 border-t border-gray-700 pt-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Show</span>
        {PAGE_SIZE_OPTIONS.map((option) => {
          const isActive = option.value === pageSize;
          return (
            <Button
              key={option.label}
              type="button"
              variant="outline"
              size="sm"
              className={
                isActive
                  ? "border-scruffy-teal text-scruffy-teal hover:bg-gray-700"
                  : "border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white"
              }
              onClick={() => onPageSizeChange(option.value)}
            >
              {option.label}
            </Button>
          );
        })}
      </div>

      <div className="flex items-center gap-3 sm:justify-end">
        <span className="text-sm text-gray-400">
          Showing {start}-{end} of {total}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white"
          disabled={isPrevDisabled}
          onClick={() => onPageChange(boundedPage - 1)}
        >
          Prev
        </Button>
        <span className="text-sm text-gray-400">
          Page {boundedPage} of {totalPages}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white"
          disabled={isNextDisabled}
          onClick={() => onPageChange(boundedPage + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
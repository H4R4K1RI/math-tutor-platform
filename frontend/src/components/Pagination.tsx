import React from 'react';

interface PaginationProps {
  total: number;
  limit: number;
  skip: number;
  onPageChange: (newSkip: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({
  total,
  limit,
  skip,
  onPageChange,
}) => {
  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center items-center gap-3 mt-6">
      <button
        onClick={() => onPageChange(skip - limit)}
        disabled={skip === 0}
        className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
      >
        ← Назад
      </button>

      <span className="text-sm text-gray-600 dark:text-gray-400">
        Страница {currentPage} из {totalPages}
      </span>

      <button
        onClick={() => onPageChange(skip + limit)}
        disabled={skip + limit >= total}
        className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
      >
        Вперёд →
      </button>
    </div>
  );
};

export default Pagination;
<?php

namespace App\Http\Helpers;

class Pagination
{
    public static function paginate($query, int $page = 1, int $pageSize = 20): array
    {
        $paginator = $query->paginate($pageSize, ['*'], 'page', $page);
        return [
            'items' => $paginator->items(),
            'total' => $paginator->total(),
            'page' => $paginator->currentPage(),
            'page_size' => $paginator->perPage(),
        ];
    }
}

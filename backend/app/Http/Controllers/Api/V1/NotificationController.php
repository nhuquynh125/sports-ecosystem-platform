<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\NotificationResource;
use App\Models\Notification;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class NotificationController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $query = Notification::where('user_id', $user->id);

        if ($request->has('is_read') && $request->is_read !== null && $request->is_read !== '') {
            $isRead = filter_var($request->is_read, FILTER_VALIDATE_BOOLEAN);
            $query->where('is_read', $isRead);
        }

        $page = max(1, (int) $request->input('page', 1));
        $pageSize = min(100, max(1, (int) $request->input('page_size', 20)));
        $total = $query->count();

        $notifications = $query->orderBy('created_at', 'desc')
            ->skip(($page - 1) * $pageSize)
            ->take($pageSize)
            ->get();

        return response()->json([
            'items' => NotificationResource::collection($notifications),
            'total' => $total,
            'page' => $page,
            'page_size' => $pageSize,
        ]);
    }

    public function read(int $id): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $notification = Notification::where('user_id', $user->id)->findOrFail($id);
        $notification->update([
            'is_read' => true,
            'read_at' => now(),
        ]);

        return response()->json(new NotificationResource($notification));
    }

    public function readAll(): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        Notification::where('user_id', $user->id)
            ->where('is_read', false)
            ->update([
                'is_read' => true,
                'read_at' => now(),
            ]);

        return response()->json(['detail' => 'All notifications marked as read']);
    }
}

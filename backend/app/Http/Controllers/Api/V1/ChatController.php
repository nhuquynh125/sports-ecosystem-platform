<?php

namespace App\Http\Controllers\Api\V1;

use App\Events\ChatMessageSent;
use App\Http\Controllers\Controller;
use App\Models\ChatMessage;
use App\Models\ChatRoom;
use App\Models\ChatRoomMember;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ChatController extends Controller
{
    public function listRooms(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $rooms = ChatRoom::whereHas('members', function ($q) use ($user) {
            $q->where('user_id', $user->id);
        })
        ->with(['members.user', 'latestMessage.sender'])
        ->get();

        return response()->json($rooms);
    }

    public function createRoom(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $validated = $request->validate([
            'type' => 'required|string|in:direct,team,tournament',
            'name' => 'nullable|string|max:150',
            'team_id' => 'nullable|integer',
            'tournament_id' => 'nullable|integer',
            'member_ids' => 'required|array',
            'member_ids.*' => 'integer|exists:users,id',
        ]);

        $room = ChatRoom::create([
            'type' => $validated['type'],
            'name' => $validated['name'] ?? null,
            'team_id' => $validated['team_id'] ?? null,
            'tournament_id' => $validated['tournament_id'] ?? null,
            'created_by' => $user->id,
        ]);

        $memberIds = array_unique(array_merge([$user->id], $validated['member_ids']));

        foreach ($memberIds as $mId) {
            ChatRoomMember::create([
                'room_id' => $room->id,
                'user_id' => $mId,
                'joined_at' => now(),
            ]);
        }

        $room->load(['members.user']);
        return response()->json($room, 201);
    }

    public function listMessages(Request $request, int $roomId): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $isMember = ChatRoomMember::where('room_id', $roomId)
            ->where('user_id', $user->id)
            ->exists();

        if (!$isMember && !$user->hasRole('admin')) {
            return response()->json(['detail' => 'Forbidden'], 403);
        }

        $query = ChatMessage::with('sender')->where('room_id', $roomId);

        if ($request->filled('before_id')) {
            $query->where('id', '<', (int) $request->before_id);
        }

        $limit = min(100, max(1, (int) $request->input('limit', 50)));
        $messages = $query->orderBy('id', 'desc')->take($limit)->get();

        // Update last read at for member
        ChatRoomMember::where('room_id', $roomId)
            ->where('user_id', $user->id)
            ->update(['last_read_at' => now()]);

        return response()->json($messages);
    }

    public function sendMessage(Request $request, int $roomId): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $isMember = ChatRoomMember::where('room_id', $roomId)
            ->where('user_id', $user->id)
            ->exists();

        if (!$isMember && !$user->hasRole('admin')) {
            return response()->json(['detail' => 'Forbidden'], 403);
        }

        $validated = $request->validate([
            'content' => 'required|string',
            'message_type' => 'nullable|string|in:text,image,system',
        ]);

        $message = ChatMessage::create([
            'room_id' => $roomId,
            'sender_id' => $user->id,
            'content' => $validated['content'],
            'message_type' => $validated['message_type'] ?? 'text',
        ]);

        $message->load('sender');

        try {
            broadcast(new ChatMessageSent($message))->toOthers();
        } catch (\Throwable $e) {
            // Broadcasting failure should not block message persistence
        }

        return response()->json($message, 201);
    }
}

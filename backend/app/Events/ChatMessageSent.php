<?php

namespace App\Events;

use App\Models\ChatMessage;
use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class ChatMessageSent implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public ChatMessage $message;

    public function __construct(ChatMessage $message)
    {
        $this->message = $message;
    }

    public function broadcastOn(): array
    {
        return [
            new PrivateChannel('chat.' . $this->message->room_id),
        ];
    }

    public function broadcastWith(): array
    {
        return [
            'id' => $this->message->id,
            'room_id' => $this->message->room_id,
            'sender_id' => $this->message->sender_id,
            'content' => $this->message->content,
            'message_type' => $this->message->message_type,
            'created_at' => $this->message->created_at?->toIso8601String(),
            'sender' => $this->message->sender ? [
                'id' => $this->message->sender->id,
                'username' => $this->message->sender->username,
                'full_name' => $this->message->sender->full_name,
                'avatar_url' => $this->message->sender->avatar_url,
            ] : null,
        ];
    }
}

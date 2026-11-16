<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ChatRoomMember extends Model
{
    protected $table = 'chat_room_members';

    public $primaryKey = null;
    public $incrementing = false;
    public $timestamps = false;

    protected $fillable = [
        'room_id',
        'user_id',
        'joined_at',
        'last_read_at',
    ];

    protected $casts = [
        'joined_at' => 'datetime',
        'last_read_at' => 'datetime',
    ];

    public function room(): BelongsTo
    {
        return $this->belongsTo(ChatRoom::class, 'room_id');
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user_id');
    }
}

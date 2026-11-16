<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class ChatRoom extends Model
{
    protected $table = 'chat_rooms';

    public $timestamps = false;

    protected $fillable = [
        'type',
        'name',
        'team_id',
        'tournament_id',
        'created_by',
        'created_at',
    ];

    protected $casts = [
        'created_at' => 'datetime',
    ];

    public function creator(): BelongsTo
    {
        return $this->belongsTo(User::class, 'created_by');
    }

    public function team(): BelongsTo
    {
        return $this->belongsTo(Team::class);
    }

    public function tournament(): BelongsTo
    {
        return $this->belongsTo(Tournament::class);
    }

    public function messages(): HasMany
    {
        return $this->hasMany(ChatMessage::class, 'room_id');
    }

    public function members(): HasMany
    {
        return $this->hasMany(ChatRoomMember::class, 'room_id');
    }
}

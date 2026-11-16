<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class ChatMessage extends Model {
    public $timestamps = false;
    protected $fillable = ['room_id', 'sender_id', 'content', 'message_type'];
    protected $dates = ['created_at', 'edited_at', 'deleted_at'];
    public function sender() { return $this->belongsTo(User::class, 'sender_id'); }
    public function room() { return $this->belongsTo(ChatRoom::class, 'room_id'); }
}

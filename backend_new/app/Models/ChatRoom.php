<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class ChatRoom extends Model {
    public $timestamps = false;
    protected $fillable = ['type', 'name', 'team_id', 'tournament_id', 'created_by'];
    public function messages() { return $this->hasMany(ChatMessage::class, 'room_id'); }
    public function members() { return $this->belongsToMany(User::class, 'chat_room_members', 'room_id', 'user_id'); }
}

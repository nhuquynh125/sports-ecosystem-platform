<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class Notification extends Model {
    protected $table = 'notifications';
    public $updatedAt = null;
    protected $fillable = ['user_id', 'type', 'title', 'body', 'data', 'is_read', 'read_at'];
    protected $casts = ['is_read' => 'boolean', 'data' => 'array', 'read_at' => 'datetime'];
    public function user() { return $this->belongsTo(User::class); }
}

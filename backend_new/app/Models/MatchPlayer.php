<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class MatchPlayer extends Model {
    protected $table = 'match_players';
    public $timestamps = false;
    protected $fillable = ['match_id', 'user_id', 'status', 'attended'];
    protected $casts = ['attended' => 'boolean'];
    public function match() { return $this->belongsTo(PickupMatch::class, 'match_id'); }
    public function user() { return $this->belongsTo(User::class); }
}

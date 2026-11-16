<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class MatchEvent extends Model {
    protected $table = 'match_events';
    public $timestamps = false;
    protected $fillable = ['match_id','player_id','team_id','event_type','minute','notes'];
    public function match() { return $this->belongsTo(TournamentMatch::class, 'match_id'); }
    public function player() { return $this->belongsTo(User::class, 'player_id'); }
    public function team() { return $this->belongsTo(Team::class); }
}

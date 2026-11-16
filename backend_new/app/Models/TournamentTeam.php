<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class TournamentTeam extends Model {
    protected $table = 'tournament_teams';
    protected $fillable = ['tournament_id','team_id','status','approved_by','approved_at'];
    protected $casts = ['approved_at' => 'datetime'];
    public function tournament() { return $this->belongsTo(Tournament::class); }
    public function team() { return $this->belongsTo(Team::class); }
}

<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class TournamentMatch extends Model {
    use HasFactory;
    protected $table = 'tournament_matches';
    protected $fillable = ['tournament_id','group_id','home_team_id','away_team_id','court_id','match_date','time_slot','home_score','away_score','status'];
    protected $casts = ['match_date' => 'date'];
    public function tournament() { return $this->belongsTo(Tournament::class); }
    public function group() { return $this->belongsTo(TournamentGroup::class, 'group_id'); }
    public function homeTeam() { return $this->belongsTo(Team::class, 'home_team_id'); }
    public function awayTeam() { return $this->belongsTo(Team::class, 'away_team_id'); }
    public function court() { return $this->belongsTo(Court::class); }
    public function events() { return $this->hasMany(MatchEvent::class, 'match_id'); }
}

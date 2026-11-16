<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Tournament extends Model {
    use HasFactory;
    protected $fillable = ['name','slug','sport_id','organizer_id','format','status','description','city','max_teams','min_teams','registration_deadline','start_date','end_date','entry_fee','prize_description'];
    protected $casts = ['registration_deadline' => 'date', 'start_date' => 'date', 'end_date' => 'date', 'entry_fee' => 'float'];
    public function sport() { return $this->belongsTo(Sport::class); }
    public function organizer() { return $this->belongsTo(User::class, 'organizer_id'); }
    public function registrations() { return $this->hasMany(TournamentTeam::class); }
    public function approvedTeams() { return $this->hasManyThrough(Team::class, TournamentTeam::class, 'tournament_id', 'id', 'id', 'team_id')->where('tournament_teams.status', 'approved'); }
    public function groups() { return $this->hasMany(TournamentGroup::class); }
    public function matches() { return $this->hasMany(TournamentMatch::class); }
}

<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class TournamentGroup extends Model {
    protected $table = 'tournament_groups';
    protected $fillable = ['tournament_id', 'name'];
    public function tournament() { return $this->belongsTo(Tournament::class); }
    public function teams() { return $this->belongsToMany(Team::class, 'group_teams', 'group_id', 'team_id'); }
    public function matches() { return $this->hasMany(TournamentMatch::class, 'group_id'); }
}

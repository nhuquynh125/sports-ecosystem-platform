<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Team extends Model {
    use HasFactory;
    protected $fillable = ['name','slug','sport_id','captain_id','description','logo_url','city','is_active'];
    protected $casts = ['is_active' => 'boolean'];
    public function sport() { return $this->belongsTo(Sport::class); }
    public function captain() { return $this->belongsTo(User::class, 'captain_id'); }
    public function members() { return $this->hasMany(TeamMember::class); }
    public function memberUsers() { return $this->belongsToMany(User::class, 'team_members', 'team_id', 'user_id')->withPivot('role'); }
}

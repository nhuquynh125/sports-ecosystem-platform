<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class PlayerProfile extends Model {
    use HasFactory;
    protected $fillable = ['user_id', 'sport_id', 'skill_level', 'position', 'city', 'bio', 'is_visible'];
    protected $casts = ['is_visible' => 'boolean'];

    public function user() { return $this->belongsTo(User::class); }
    public function sport() { return $this->belongsTo(Sport::class); }
    public function availability() { return $this->hasMany(PlayerAvailability::class, 'player_profile_id'); }
}

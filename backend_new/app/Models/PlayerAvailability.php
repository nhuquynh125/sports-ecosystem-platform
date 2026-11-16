<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class PlayerAvailability extends Model {
    protected $table = 'player_availability';
    protected $fillable = ['player_profile_id', 'day_of_week', 'start_time', 'end_time'];
    public function profile() { return $this->belongsTo(PlayerProfile::class, 'player_profile_id'); }
}

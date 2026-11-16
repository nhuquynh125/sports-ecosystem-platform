<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class PickupMatch extends Model {
    use HasFactory;
    protected $table = 'pickup_matches';
    protected $fillable = ['host_id','sport_id','title','description','area','location_detail','latitude','longitude','match_date','time_slot','duration_minutes','max_players','skill_level','status','chat_room_id'];
    protected $casts = ['match_date' => 'date', 'latitude' => 'float', 'longitude' => 'float'];
    public function host() { return $this->belongsTo(User::class, 'host_id'); }
    public function sport() { return $this->belongsTo(Sport::class); }
    public function players() { return $this->hasMany(MatchPlayer::class, 'match_id'); }
    public function playerUsers() { return $this->belongsToMany(User::class, 'match_players', 'match_id', 'user_id')->withPivot('status', 'attended', 'joined_at'); }
    public function ratings() { return $this->hasMany(PickupRating::class, 'match_id'); }
    public function chatRoom() { return $this->belongsTo(ChatRoom::class, 'chat_room_id'); }
}

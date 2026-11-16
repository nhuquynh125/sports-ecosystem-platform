<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class PickupRating extends Model {
    protected $table = 'pickup_ratings';
    public $timestamps = false;
    protected $fillable = ['match_id','rater_id','rated_user_id','skill_score','punctuality_score','comment'];
    public function match() { return $this->belongsTo(PickupMatch::class, 'match_id'); }
    public function rater() { return $this->belongsTo(User::class, 'rater_id'); }
    public function ratedUser() { return $this->belongsTo(User::class, 'rated_user_id'); }
}

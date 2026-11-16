<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Court extends Model {
    use HasFactory;
    protected $fillable = ['venue_id','sport_id','name','surface_type','has_lighting','price_per_slot','slot_duration_minutes','is_active'];
    protected $casts = ['is_active' => 'boolean', 'has_lighting' => 'boolean', 'price_per_slot' => 'float'];
    public function venue() { return $this->belongsTo(Venue::class); }
    public function sport() { return $this->belongsTo(Sport::class); }
    public function bookings() { return $this->hasMany(Booking::class); }
}

<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Booking extends Model {
    use HasFactory;
    protected $fillable = ['court_id','user_id','booking_date','time_slot','duration_slots','status','total_price','notes'];
    protected $casts = ['booking_date' => 'date', 'total_price' => 'float'];
    public function court() { return $this->belongsTo(Court::class); }
    public function user() { return $this->belongsTo(User::class); }
}

<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Venue extends Model {
    use HasFactory;
    protected $fillable = ['owner_id','name','description','address','city','district','latitude','longitude','phone','open_time','close_time','is_active'];
    protected $casts = ['is_active' => 'boolean', 'latitude' => 'float', 'longitude' => 'float'];
    public function owner() { return $this->belongsTo(User::class, 'owner_id'); }
    public function courts() { return $this->hasMany(Court::class); }
}

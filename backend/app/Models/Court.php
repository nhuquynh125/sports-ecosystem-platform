<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Court extends Model
{
    protected $table = 'courts';

    protected $fillable = [
        'venue_id',
        'sport_id',
        'name',
        'surface_type',
        'capacity',
        'hourly_price',
        'is_active',
    ];

    protected $casts = [
        'hourly_price' => 'decimal:2',
        'capacity' => 'integer',
        'is_active' => 'boolean',
    ];

    public function venue(): BelongsTo
    {
        return $this->belongsTo(Venue::class);
    }

    public function sport(): BelongsTo
    {
        return $this->belongsTo(Sport::class);
    }

    public function bookings(): HasMany
    {
        return $this->hasMany(Booking::class);
    }
}

<?php

namespace App\Models;

use Carbon\Carbon;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Booking extends Model
{
    protected $table = 'bookings';

    protected $fillable = [
        'booking_code',
        'court_id',
        'user_id',
        'booking_date',
        'time_slot',
        'total_price',
        'status',
        'note',
        'cancelled_at',
        'cancel_reason',
    ];

    protected $casts = [
        'booking_date' => 'date',
        'total_price' => 'decimal:2',
        'cancelled_at' => 'datetime',
    ];

    protected $appends = [
        'end_time',
        'venue_id',
        'venue_name',
        'court_name',
    ];

    public function court(): BelongsTo
    {
        return $this->belongsTo(Court::class);
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function getEndTimeAttribute(): string
    {
        // 1-hour slots
        $start = Carbon::createFromFormat('H:i:s', $this->time_slot);
        return $start->addHour()->format('H:i:s');
    }

    public function getVenueIdAttribute(): int
    {
        return $this->court ? (int) $this->court->venue_id : 0;
    }

    public function getVenueNameAttribute(): string
    {
        return $this->court && $this->court->venue ? $this->court->venue->name : '';
    }

    public function getCourtNameAttribute(): string
    {
        return $this->court ? $this->court->name : '';
    }
}

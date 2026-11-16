<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class PlayerAvailability extends Model
{
    protected $table = 'player_availability';

    public $timestamps = false;

    protected $fillable = [
        'player_profile_id',
        'day_of_week',
        'start_time',
        'end_time',
        'created_at',
    ];

    protected $casts = [
        'day_of_week' => 'integer',
        'created_at' => 'datetime',
    ];

    public function playerProfile(): BelongsTo
    {
        return $this->belongsTo(PlayerProfile::class, 'player_profile_id');
    }
}

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class PlayerProfile extends Model
{
    protected $table = 'player_profiles';

    protected $fillable = [
        'user_id',
        'sport_id',
        'position',
        'skill_level',
        'preferred_side',
        'height_cm',
        'weight_kg',
        'city',
        'bio',
        'is_visible',
    ];

    protected $casts = [
        'is_visible' => 'boolean',
        'height_cm' => 'integer',
        'weight_kg' => 'decimal:2',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function sport(): BelongsTo
    {
        return $this->belongsTo(Sport::class);
    }

    public function availability(): HasMany
    {
        return $this->hasMany(PlayerAvailability::class, 'player_profile_id');
    }
}

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Sport extends Model
{
    protected $table = 'sports';

    protected $fillable = [
        'name',
        'slug',
        'description',
        'icon_url',
        'is_active',
    ];

    protected $casts = [
        'is_active' => 'boolean',
    ];

    public function playerProfiles(): HasMany
    {
        return $this->hasMany(PlayerProfile::class);
    }

    public function courts(): HasMany
    {
        return $this->hasMany(Court::class);
    }

    public function teams(): HasMany
    {
        return $this->hasMany(Team::class);
    }

    public function tournaments(): HasMany
    {
        return $this->hasMany(Tournament::class);
    }

    public function pickupMatches(): HasMany
    {
        return $this->hasMany(PickupMatch::class);
    }
}

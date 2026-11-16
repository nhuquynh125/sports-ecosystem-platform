<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Venue extends Model
{
    protected $table = 'venues';

    protected $fillable = [
        'owner_id',
        'name',
        'description',
        'address',
        'city',
        'district',
        'latitude',
        'longitude',
        'phone',
        'open_time',
        'close_time',
        'is_active',
    ];

    protected $casts = [
        'is_active' => 'boolean',
        'latitude' => 'decimal:6',
        'longitude' => 'decimal:6',
    ];

    public function owner(): BelongsTo
    {
        return $this->belongsTo(User::class, 'owner_id');
    }

    public function courts(): HasMany
    {
        return $this->hasMany(Court::class);
    }

    public function scopeActive($query)
    {
        return $query->where('is_active', true);
    }

    public function getActiveCourtsAttribute()
    {
        return $this->courts()->where('is_active', true)->get();
    }
}

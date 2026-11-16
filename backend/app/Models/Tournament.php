<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Tournament extends Model
{
    protected $table = 'tournaments';

    protected $fillable = [
        'organizer_id',
        'sport_id',
        'name',
        'slug',
        'description',
        'format',
        'status',
        'max_teams',
        'start_date',
        'end_date',
        'venue_id',
        'prize_info',
        'entry_fee',
    ];

    protected $casts = [
        'max_teams' => 'integer',
        'start_date' => 'date',
        'end_date' => 'date',
        'entry_fee' => 'decimal:2',
    ];

    public function organizer(): BelongsTo
    {
        return $this->belongsTo(User::class, 'organizer_id');
    }

    public function sport(): BelongsTo
    {
        return $this->belongsTo(Sport::class);
    }

    public function venue(): BelongsTo
    {
        return $this->belongsTo(Venue::class);
    }

    public function tournamentTeams(): HasMany
    {
        return $this->hasMany(TournamentTeam::class);
    }

    public function groups(): HasMany
    {
        return $this->hasMany(TournamentGroup::class);
    }

    public function matches(): HasMany
    {
        return $this->hasMany(TournamentMatch::class);
    }
}

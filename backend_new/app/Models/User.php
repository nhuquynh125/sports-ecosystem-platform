<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use PHPOpenSourceSaver\JWTAuth\Contracts\JWTSubject;

class User extends Authenticatable implements JWTSubject
{
    use HasFactory, Notifiable;

    protected $table = 'users';

    protected $fillable = [
        'email', 'username', 'password_hash', 'full_name',
        'phone', 'avatar_url', 'date_of_birth', 'is_active',
        'allow_scouting', 'last_login_at',
    ];

    protected $hidden = ['password_hash', 'remember_token'];

    protected $casts = [
        'is_active'       => 'boolean',
        'allow_scouting'  => 'boolean',
        'date_of_birth'   => 'date',
        'last_login_at'   => 'datetime',
        'email_verified_at' => 'datetime',
    ];

    // Disable default password field — we use password_hash
    public function getAuthPassword(): string
    {
        return $this->password_hash;
    }

    // JWT Subject interface
    public function getJWTIdentifier(): mixed
    {
        return $this->getKey();
    }

    public function getJWTCustomClaims(): array
    {
        return [
            'roles' => $this->roles->pluck('name')->toArray(),
        ];
    }

    // Relationships
    public function roles()
    {
        return $this->belongsToMany(Role::class, 'user_roles', 'user_id', 'role_id')
                    ->withPivot('assigned_at', 'assigned_by');
    }

    public function playerProfile()
    {
        return $this->hasOne(PlayerProfile::class, 'user_id');
    }

    public function notifications()
    {
        return $this->hasMany(Notification::class, 'user_id');
    }
}

<?php
namespace App\Http\Resources;

use Illuminate\Http\Resources\Json\JsonResource;

class UserResource extends JsonResource
{
    public function toArray($request): array
    {
        return [
            'id'             => $this->id,
            'email'          => $this->email,
            'username'       => $this->username,
            'full_name'      => $this->full_name,
            'phone'          => $this->phone,
            'avatar_url'     => $this->avatar_url,
            'date_of_birth'  => $this->date_of_birth?->toDateString(),
            'is_active'      => $this->is_active,
            'allow_scouting' => $this->allow_scouting,
            'roles'          => $this->whenLoaded('roles', fn() => $this->roles->pluck('name')),
            'last_login_at'  => $this->last_login_at?->toIso8601String(),
            'created_at'     => $this->created_at?->toIso8601String(),
            'updated_at'     => $this->updated_at?->toIso8601String(),
        ];
    }
}

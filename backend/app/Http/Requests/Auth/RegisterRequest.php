<?php

namespace App\Http\Requests\Auth;

use Illuminate\Foundation\Http\FormRequest;

class RegisterRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'email' => 'required|email|unique:users,email',
            'username' => 'required|string|min:3|max:50|unique:users,username',
            'password' => 'required|string|min:8',
            'full_name' => 'required|string|max:150',
            'role' => 'required|string|in:admin,player,venue_owner,organizer,coach',
        ];
    }
}

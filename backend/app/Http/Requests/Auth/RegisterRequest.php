<?php
namespace App\Http\Requests\Auth;

use Illuminate\Foundation\Http\FormRequest;

class RegisterRequest extends FormRequest
{
    public function authorize(): bool { return true; }

    public function rules(): array
    {
        return [
            'email'     => ['required', 'email', 'max:254', 'unique:users,email'],
            'username'  => ['required', 'string', 'min:3', 'max:50', 'unique:users,username', 'regex:/^[A-Za-z0-9_.\-]+$/'],
            'password'  => ['required', 'string', 'min:8', 'max:128', 'regex:/^(?=.*[a-zA-Z])(?=.*[0-9]).+$/'],
            'full_name' => ['required', 'string', 'min:1', 'max:150'],
            'role'      => ['sometimes', 'string', 'in:player,venue_owner,organizer,coach'],
        ];
    }

    public function messages(): array
    {
        return [
            'password.regex' => 'Password must contain both letters and digits.',
            'username.regex' => "Username may only contain letters, digits, '_', '.' and '-'.",
        ];
    }
}

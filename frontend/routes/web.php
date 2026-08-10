<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\BotController;
use App\Http\Controllers\AuthController;

// --- Authentication (guests only) ---
Route::middleware('guest')->group(function () {
    Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
    Route::post('/login', [AuthController::class, 'login'])->name('login.attempt');
    Route::get('/register', [AuthController::class, 'showRegister'])->name('register');
    Route::post('/register', [AuthController::class, 'register'])->name('register.attempt');
});

Route::post('/logout', [AuthController::class, 'logout'])
    ->middleware('auth')
    ->name('logout');

// --- Everything below requires a signed-in user ---
Route::middleware('auth')->group(function () {

    // Dashboard
    Route::get('/', [BotController::class, 'index'])->name('dashboard');
    Route::get('/dashboard', [BotController::class, 'index']);

    // Bot Configuration
    Route::get('/bot-config/{id}', [BotController::class, 'edit'])->name('bot-config');
    Route::get('/bot-config', function () {
        return redirect()->route('bot-config', ['id' => 'new']);
    });

    // Knowledge Base
    Route::get('/bots/{id}/knowledge', [BotController::class, 'knowledge'])->name('knowledge');
    // Test Preview
    Route::get('/test-preview/{id}', [BotController::class, 'showPreview'])->name('preview');
    // API-Proxy Routes (create uses id "new", update uses an existing bot id)
    Route::post('/bots/update/{id}', [BotController::class, 'update'])->name('bots.update');
    Route::delete('/bots/delete/{id}', [BotController::class, 'destroy'])->name('bots.destroy');

    // Static Pages
    Route::get('/documentation', [BotController::class, 'documentation'])->name('documentation');
    Route::get('/account', [BotController::class, 'account'])->name('account');
    Route::get('/integrations', [BotController::class, 'integrations'])->name('integrations');
    Route::get('/integrations/status', [BotController::class, 'integrationStatus'])->name('integrations.status');
    Route::get('/integrations/{provider}/connect', [BotController::class, 'connectIntegration'])->name('integrations.connect');
    Route::delete('/integrations/{provider}', [BotController::class, 'disconnectIntegration'])->name('integrations.disconnect');
    Route::get('/filter', function () { return back(); })->name('filter');
});

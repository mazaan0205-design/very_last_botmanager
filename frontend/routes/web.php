<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\BotController;

// Dashboard
Route::get('/', [BotController::class, 'index'])->name('dashboard');
Route::get('/dashboard', [BotController::class, 'index']);

// Bot Configuration
Route::get('/bot-config/{id}', [BotController::class, 'edit'])->name('bot-config');
Route::get('/bot-config', function () {
    return redirect()->route('bot-config', ['id' => 'new']);
});

// Knowledge Base
// Fixed: Parameter in route matches the variable in BotController
Route::get('/bots/{id}/knowledge', [BotController::class, 'knowledge'])->name('knowledge');
// Test Preview
// Fixed: Parameter in route matches the variable in BotController
Route::get('/test-preview/{id}', [BotController::class, 'showPreview'])->name('preview');
// API-Proxy Routes
Route::post('/bots/update/{id}', [BotController::class, 'update'])->name('bots.update');
Route::delete('/bots/delete/{id}', [BotController::class, 'destroy'])->name('bots.destroy');

// Static Pages
Route::get('/documentation', [BotController::class, 'documentation'])->name('documentation');
Route::get('/account', [BotController::class, 'account'])->name('account');
Route::get('/filter', function () { return back(); })->name('filter');

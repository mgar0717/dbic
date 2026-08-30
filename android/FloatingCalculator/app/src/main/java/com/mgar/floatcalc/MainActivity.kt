package com.mgar.floatcalc

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView

class MainActivity : Activity() {

    private lateinit var statusText: TextView
    private lateinit var toggleButton: Button

    private val overlayPermissionRequest = 1001

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.statusText)
        toggleButton = findViewById(R.id.toggleButton)

        toggleButton.setOnClickListener {
            if (FloatingCalcService.isRunning) {
                stopService(Intent(this, FloatingCalcService::class.java))
                refreshStatus()
            } else {
                requestOverlayPermissionThenStart()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
    }

    private fun refreshStatus() {
        val running = FloatingCalcService.isRunning
        statusText.text = getString(if (running) R.string.status_running else R.string.status_stopped)
        toggleButton.text = getString(if (running) R.string.btn_stop else R.string.btn_start)
    }

    private fun requestOverlayPermissionThenStart() {
        if (Settings.canDrawOverlays(this)) {
            startFloatingService()
            return
        }
        val intent = Intent(
            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
            Uri.parse("package:$packageName")
        )
        @Suppress("DEPRECATION")
        startActivityForResult(intent, overlayPermissionRequest)
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == overlayPermissionRequest && Settings.canDrawOverlays(this)) {
            startFloatingService()
        }
    }

    private fun startFloatingService() {
        startService(Intent(this, FloatingCalcService::class.java))
        refreshStatus()
    }
}

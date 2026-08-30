package com.mgar.floatcalc

import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.PixelFormat
import android.os.IBinder
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import android.widget.SeekBar
import android.widget.TextView
import kotlin.math.roundToInt

class FloatingCalcService : Service() {

    companion object {
        private const val PREFS = "floating_calc_prefs"
        private const val KEY_X = "pos_x"
        private const val KEY_Y = "pos_y"
        private const val KEY_ALPHA = "alpha_percent"
        private const val KEY_COLLAPSED = "collapsed"

        @Volatile
        var isRunning: Boolean = false
            private set
    }

    private lateinit var windowManager: WindowManager
    private lateinit var prefs: SharedPreferences
    private var floatingView: View? = null
    private lateinit var params: WindowManager.LayoutParams
    private val calcEngine = CalcEngine()

    override fun onBind(intent: Intent?): IBinder? = null

    // 알림 없는 일반 서비스로 동작한다. 포그라운드 서비스가 아니므로 상시 알림이 뜨지 않는 대신,
    // 화면이 오래 꺼져 있거나 메모리가 부족하면 시스템이 이 서비스를 종료시킬 수 있다.
    override fun onCreate() {
        super.onCreate()
        isRunning = true
        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        addFloatingView()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        isRunning = false
        floatingView?.let {
            runCatching { windowManager.removeView(it) }
        }
        floatingView = null
    }

    // ---------------- 플로팅 뷰 ----------------

    private fun addFloatingView() {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_calculator, null)
        floatingView = view

        val savedAlpha = prefs.getInt(KEY_ALPHA, 95).coerceIn(20, 100)
        val savedCollapsed = prefs.getBoolean(KEY_COLLAPSED, false)

        val overlayType = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY

        params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            overlayType,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = prefs.getInt(KEY_X, 60)
            y = prefs.getInt(KEY_Y, 200)
        }

        // 투명도는 윈도우(params.alpha)가 아니라 뷰 자체의 alpha로 처리한다.
        // params.alpha를 낮추면 일부 기기(Android 12+ 탭재킹 방지 정책 등)에서
        // 오버레이 창의 터치 입력이 통째로 막히는 문제가 있다.
        view.alpha = savedAlpha / 100f

        windowManager.addView(view, params)

        setupCalculatorKeys(view)
        setupHeaderControls(view, savedAlpha, savedCollapsed)
    }

    private fun setupCalculatorKeys(root: View) {
        val displayText = root.findViewById<TextView>(R.id.displayText)
        val expressionText = root.findViewById<TextView>(R.id.expressionText)
        displayText.text = calcEngine.display
        expressionText.text = calcEngine.expression

        val bodyContainer = root.findViewById<View>(R.id.bodyContainer)
        forEachButtonWithTag(bodyContainer) { button ->
            button.setOnClickListener {
                val tag = it.tag as? String ?: return@setOnClickListener
                displayText.text = calcEngine.input(tag)
                expressionText.text = calcEngine.expression
            }
        }
    }

    private fun forEachButtonWithTag(view: View, action: (View) -> Unit) {
        if (view is android.view.ViewGroup) {
            for (i in 0 until view.childCount) {
                forEachButtonWithTag(view.getChildAt(i), action)
            }
        } else if (view.tag is String) {
            action(view)
        }
    }

    private fun setupHeaderControls(root: View, initialAlpha: Int, initialCollapsed: Boolean) {
        val headerRow = root.findViewById<View>(R.id.headerRow)
        val bodyContainer = root.findViewById<View>(R.id.bodyContainer)
        val opacityRow = root.findViewById<View>(R.id.opacityRow)
        val opacitySeekBar = root.findViewById<SeekBar>(R.id.opacitySeekBar)
        val opacityValueText = root.findViewById<TextView>(R.id.opacityValueText)
        val opacityToggle = root.findViewById<ImageButton>(R.id.opacityToggle)
        val collapseToggle = root.findViewById<ImageButton>(R.id.collapseToggle)
        val closeButton = root.findViewById<ImageButton>(R.id.closeButton)

        opacitySeekBar.progress = initialAlpha
        opacityValueText.text = "$initialAlpha%"

        var collapsed = initialCollapsed
        fun applyCollapsed() {
            bodyContainer.visibility = if (collapsed) View.GONE else View.VISIBLE
            if (collapsed) opacityRow.visibility = View.GONE
            collapseToggle.setImageResource(
                if (collapsed) R.drawable.ic_chevron_down else R.drawable.ic_chevron_up
            )
        }
        applyCollapsed()

        collapseToggle.setOnClickListener {
            collapsed = !collapsed
            applyCollapsed()
            prefs.edit().putBoolean(KEY_COLLAPSED, collapsed).apply()
        }

        opacityToggle.setOnClickListener {
            opacityRow.visibility = if (opacityRow.visibility == View.VISIBLE) View.GONE else View.VISIBLE
        }

        opacitySeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                val percent = progress.coerceIn(20, 100)
                opacityValueText.text = "$percent%"
                root.alpha = percent / 100f
            }

            override fun onStartTrackingTouch(seekBar: SeekBar?) {}

            override fun onStopTrackingTouch(seekBar: SeekBar?) {
                prefs.edit().putInt(KEY_ALPHA, seekBar?.progress ?: 95).apply()
            }
        })

        closeButton.setOnClickListener { stopSelf() }

        setupDrag(headerRow)
    }

    private fun setupDrag(handle: View) {
        var initialX = 0
        var initialY = 0
        var initialTouchX = 0f
        var initialTouchY = 0f
        var moved = false

        handle.setOnTouchListener { v, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    moved = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - initialTouchX)
                    val dy = (event.rawY - initialTouchY)
                    if (dx * dx + dy * dy > 25f) moved = true
                    params.x = initialX + dx.roundToInt()
                    params.y = initialY + dy.roundToInt()
                    runCatching { windowManager.updateViewLayout(floatingView, params) }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (moved) {
                        prefs.edit().putInt(KEY_X, params.x).putInt(KEY_Y, params.y).apply()
                    } else {
                        v.performClick()
                    }
                    true
                }
                else -> false
            }
        }
    }
}

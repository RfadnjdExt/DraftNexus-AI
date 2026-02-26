package com.draftnexus.ai

import com.draftnexus.ai.core.model.*
import com.draftnexus.ai.core.ui.DraftScreen
import com.draftnexus.ai.core.domain.GetHeroesUseCase
import com.draftnexus.ai.core.domain.GetRecommendationsUseCase
import com.draftnexus.ai.core.domain.LoadResourcesUseCase
import com.draftnexus.ai.feature.draft.DraftViewModel
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject
import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.os.IBinder
import android.view.Gravity
import android.view.WindowManager
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.lifecycle.ViewModelStore
import androidx.lifecycle.ViewModelStoreOwner
import androidx.lifecycle.setViewTreeLifecycleOwner
import androidx.savedstate.SavedStateRegistry
import androidx.savedstate.SavedStateRegistryController
import androidx.savedstate.SavedStateRegistryOwner
import androidx.savedstate.setViewTreeSavedStateRegistryOwner

@AndroidEntryPoint
class OverlayService : Service(), LifecycleOwner, ViewModelStoreOwner, SavedStateRegistryOwner {

    private val lifecycleRegistry = LifecycleRegistry(this)
    private val savedStateRegistryController = SavedStateRegistryController.create(this)
    private val store = ViewModelStore()
    
    override val lifecycle: Lifecycle get() = lifecycleRegistry
    override val savedStateRegistry: SavedStateRegistry get() = savedStateRegistryController.savedStateRegistry
    override val viewModelStore: ViewModelStore get() = store

    private lateinit var windowManager: WindowManager
    private var composeView: ComposeView? = null
    @Inject
    lateinit var getHeroesUseCase: GetHeroesUseCase
    @Inject
    lateinit var getRecommendationsUseCase: GetRecommendationsUseCase
    @Inject
    lateinit var loadResourcesUseCase: LoadResourcesUseCase

    private lateinit var viewModel: DraftViewModel
    private lateinit var params: WindowManager.LayoutParams
    private var isViewAdded = false

    override fun onCreate() {
        super.onCreate()
        android.util.Log.d("DraftNexus", "OverlayService onCreate started")
        
        // Start Foreground immediately to prevent crash
        startForegroundServiceNotification()
        
        savedStateRegistryController.performRestore(null)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_CREATE)
        
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        viewModel = DraftViewModel(getHeroesUseCase, getRecommendationsUseCase, loadResourcesUseCase)

        setupOverlayView()
        
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_START)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)
    }

    private fun setupOverlayView() {
        // Guard: don't add a duplicate view
        if (isViewAdded) return

        val view = ComposeView(this).apply {
            setViewTreeLifecycleOwner(this@OverlayService)
            setViewTreeSavedStateRegistryOwner(this@OverlayService)
            
            setContent {
                var isMinimizedState by remember { mutableStateOf(false) }
                
                MaterialTheme(
                    colorScheme = darkColorScheme(
                        background = Color(0xEE1E1E1E), // More opaque background
                        surface = Color(0xEE262730),
                        primary = Color(0xFFBB86FC),
                        onBackground = Color.White,
                        onSurface = Color.White
                    )
                ) {
                    Surface(
                        modifier = if (isMinimizedState) Modifier.wrapContentSize() else Modifier.fillMaxSize(),
                        color = if (isMinimizedState) Color.Transparent else Color(0xEE1A1A1A), // Transparent when minimized
                        shape = RoundedCornerShape(16.dp)
                    ) {
                        // Re-use DraftScreen. 
                        val state by viewModel.uiState.collectAsState()
                        Box(modifier = Modifier.padding(if (isMinimizedState) 0.dp else 8.dp)) {
                            DraftScreen(
                                state = state,
                                onAllySelected = viewModel::selectAlly,
                                onEnemySelected = viewModel::selectEnemy,
                                onClearDraft = viewModel::clearDraft,
                                isOverlay = true,
                                onCloseOverlay = { stopSelf() },
                                onDrag = { dx, dy ->
                                    params.x += dx.toInt()
                                    params.y += dy.toInt()
                                    composeView?.let { windowManager.updateViewLayout(it, params) }
                                },
                                onMinimizedChange = { isMinimized ->
                                    isMinimizedState = isMinimized
                                    // Resize window based on minimized state and orientation
                                    val metrics = resources.displayMetrics
                                    val isLandscape = resources.configuration.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE
                                    
                                    if (isMinimized) {
                                        params.width = WindowManager.LayoutParams.WRAP_CONTENT
                                        params.height = WindowManager.LayoutParams.WRAP_CONTENT
                                    } else {
                                        // Target height to fit 3 rows: ~350-400dp
                                        val density = metrics.density
                                        val targetHeight = if (isLandscape) (400 * density).toInt() else (metrics.heightPixels * 0.7).toInt()
                                        params.height = targetHeight.coerceAtMost((metrics.heightPixels * 0.95).toInt())
                                        params.width = if (isLandscape) (metrics.widthPixels * 0.35).toInt() else (metrics.widthPixels * 0.9).toInt()
                                    }
                                    composeView?.let { windowManager.updateViewLayout(it, params) }
                                },
                                onHeroSelectorVisibilityChange = { isVisible ->
                                    if (isVisible) {
                                        params.flags = params.flags and WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE.inv()
                                    } else {
                                        params.flags = params.flags or WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                                    }
                                    composeView?.let { windowManager.updateViewLayout(it, params) }
                                }
                            )
                        }
                    }
                }
            }
        }
        composeView = view

        val layoutFlag = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY

        params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT, 
            900, 
            layoutFlag,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or 
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        )
        
        params.gravity = Gravity.TOP or Gravity.START
        
        val metrics = resources.displayMetrics
        val isLandscape = resources.configuration.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE
        
        // Width: 35% in Landscape, 90% in Portrait
        params.width = if (isLandscape) (metrics.widthPixels * 0.35).toInt() else (metrics.widthPixels * 0.9).toInt()
        
        // Height: 90% in Landscape, 70% in Portrait
        params.height = if (isLandscape) (metrics.heightPixels * 0.9).toInt() else (metrics.heightPixels * 0.7).toInt()
        
        // Simple positioning (Top-Left + Offset)
        params.x = 20
        params.y = 100

        try {
            android.util.Log.d("DraftNexus", "Attempting to addView to WindowManager")
            windowManager.addView(view, params)
            isViewAdded = true
            android.util.Log.d("DraftNexus", "addView successful")
        } catch (e: Exception) {
            android.util.Log.e("DraftNexus", "Error adding view: ${e.message}", e)
        }
    }

    private fun startForegroundServiceNotification() {
        val channelId = "overlay_channel"
        val channel = android.app.NotificationChannel(
            channelId,
            "DraftNexus Overlay",
            android.app.NotificationManager.IMPORTANCE_LOW
        )
        getSystemService(android.app.NotificationManager::class.java).createNotificationChannel(channel)

        val notification = android.app.Notification.Builder(this, channelId)
            .setContentTitle("DraftNexus AI Overlay")
            .setContentText("Tap to open app")
            .setSmallIcon(android.R.drawable.sym_def_app_icon)
            .build()

        startForeground(1, notification)
    }

    override fun onConfigurationChanged(newConfig: android.content.res.Configuration) {
        super.onConfigurationChanged(newConfig)
        
        val metrics = resources.displayMetrics
        val isLandscape = newConfig.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE
        
        // Update width/height based on orientation
        // Update width/height based on orientation
        // Width: 1/3 screen (approx 35%) in Landscape
        params.width = if (isLandscape) (metrics.widthPixels * 0.35).toInt() else (metrics.widthPixels * 0.9).toInt()
        
        // Height: Maximize vertical space (95%) in Landscape
        val targetHeight = if (isLandscape) (metrics.heightPixels * 0.95).toInt() else (metrics.heightPixels * 0.7).toInt()
        
        params.height = targetHeight
        
        composeView?.let { windowManager.updateViewLayout(it, params) }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        android.util.Log.d("DraftNexus", "OverlayService onStartCommand (isViewAdded=$isViewAdded)")
        if (!isViewAdded) {
            setupOverlayView()
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY)
        store.clear()
        if (isViewAdded && composeView != null) {
            windowManager.removeView(composeView)
            composeView = null
            isViewAdded = false
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

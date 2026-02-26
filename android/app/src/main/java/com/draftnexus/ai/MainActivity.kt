

package com.draftnexus.ai

import android.os.Bundle
import com.draftnexus.ai.core.model.*
import com.draftnexus.ai.core.ui.DraftScreen
import com.draftnexus.ai.feature.draft.DraftViewModel
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    private val viewModel: DraftViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    background = Color(0xFF0F0F0F), // YouTube pure dark
                    surface = Color(0xFF212121),    // YouTube surface gray
                    primary = Color(0xFFF1F1F1),    // High-contrast white for primary text/icons
                    secondary = Color(0xFFAAAAAA),  // Secondary text gray
                    onBackground = Color(0xFFF1F1F1),
                    onSurface = Color(0xFFF1F1F1)
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val state by viewModel.uiState.collectAsState()
                    PermissionLauncherScreen(
                        state = state,
                        onAllySelected = viewModel::selectAlly,
                        onEnemySelected = viewModel::selectEnemy,
                        onClearDraft = viewModel::clearDraft
                    )
                }
            }
        }
    }
}

@Composable
fun PermissionLauncherScreen(
    state: DraftState,
    onAllySelected: (Int, Hero?) -> Unit,
    onEnemySelected: (Int, Hero?) -> Unit,
    onClearDraft: () -> Unit
) {
    val context = LocalContext.current
    var hasPermission by remember { mutableStateOf(false) }

    var resumeTrigger by remember { mutableLongStateOf(0L) }
    
    // Check permission on resume/start
    val lifecycleOwner = androidx.compose.ui.platform.LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->
            if (event == androidx.lifecycle.Lifecycle.Event.ON_RESUME) {
                 hasPermission = android.provider.Settings.canDrawOverlays(context)
                 if (hasPermission) {
                     resumeTrigger = System.currentTimeMillis()
                 }
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    LaunchedEffect(resumeTrigger) {
        if (hasPermission && resumeTrigger > 0) {
            // Start Service
            val intent = android.content.Intent(context, OverlayService::class.java)
            context.startForegroundService(intent)
            // Close Activity / Minimize
             (context as? android.app.Activity)?.moveTaskToBack(true)
        }
    }

    if (hasPermission) {
        DraftScreen(
            state = state,
            onAllySelected = onAllySelected,
            onEnemySelected = onEnemySelected,
            onClearDraft = onClearDraft
        )
    } else {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("DraftNexus AI", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color.White)
            Spacer(modifier = Modifier.height(16.dp))
            Text("Overlay Permission Required", color = Color.Gray)
            Spacer(modifier = Modifier.height(16.dp))
            Button(
                onClick = {
                    val intent = android.content.Intent(
                        android.provider.Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        android.net.Uri.parse("package:${context.packageName}")
                    )
                    context.startActivity(intent)
                },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3EA6FF)), 
                shape = RoundedCornerShape(18.dp)
            ) {
                Text("Grant Overlay Permission", color = Color(0xFF0F0F0F), fontWeight = FontWeight.Bold)
            }
        }
    }
}

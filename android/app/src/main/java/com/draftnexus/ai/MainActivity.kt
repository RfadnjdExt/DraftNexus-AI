

package com.draftnexus.ai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import kotlinx.coroutines.launch

import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    private val viewModel: DraftViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    background = Color(0xFF1E1E1E),
                    surface = Color(0xFF262730),
                    primary = Color(0xFFBB86FC),
                    onBackground = Color.White,
                    onSurface = Color.White
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    PermissionLauncherScreen(viewModel)
                }
            }
        }
    }
}

@Composable
fun PermissionLauncherScreen(viewModel: DraftViewModel) {
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
            android.util.Log.d("DraftNexus", "Attempting to start foreground service (Trigger: $resumeTrigger)")
            try {
                context.startForegroundService(intent)
                android.util.Log.d("DraftNexus", "startForegroundService called successfully")
            } catch (e: Exception) {
                android.util.Log.e("DraftNexus", "Failed to start service: ${e.message}")
            }
            // Close Activity / Minimize
             (context as? android.app.Activity)?.moveTaskToBack(true)
        }
    }

    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("DraftNexus AI", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))
        
        if (!hasPermission) {
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
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFBB86FC))
            ) {
                Text("Grant Overlay Permission")
            }
        } else {
            Text("Launching Overlay...", color = Color.Green)
        }
    }
}

@Composable
fun DraftScreen(
    viewModel: DraftViewModel,
    isOverlay: Boolean = false,
    onCloseOverlay: (() -> Unit)? = null,
    onDrag: ((Float, Float) -> Unit)? = null, // dx, dy delta
    onMinimizedChange: ((Boolean) -> Unit)? = null, // notify when minimized state changes
    onHeroSelectorVisibilityChange: ((Boolean) -> Unit)? = null // notify when hero selector opens/closes
) {
    val state by viewModel.uiState.collectAsState()
    var showHeroSelector by remember { mutableStateOf(false) }
    
    // Notify parent when hero selector visibility changes
    LaunchedEffect(showHeroSelector) {
        onHeroSelectorVisibilityChange?.invoke(showHeroSelector)
    }

    var selectionMode by remember { mutableStateOf<SelectionMode?>(null) }
    
    // Hoisted State for Hero Selector Persistence
    var selectorTabIndex by remember { mutableIntStateOf(0) }
    val selectorScrollState = androidx.compose.foundation.lazy.grid.rememberLazyGridState()
    
    // Shrink/Expand State for Overlay
    var isMinimized by remember { mutableStateOf(false) }
    
    // Notify parent when minimized changes
    LaunchedEffect(isMinimized) {
        onMinimizedChange?.invoke(isMinimized)
    }
    
    // Snackbar state
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    Box(modifier = Modifier.fillMaxSize()) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Drag Bar (outside LazyColumn to prevent scroll conflict)
            if (isOverlay) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = if (isMinimized) 8.dp else 16.dp)
                        .padding(top = if (isMinimized) 8.dp else 16.dp)
                        .height(28.dp)
                        .background(Color(0xFF555555), RoundedCornerShape(4.dp))
                        .pointerInput(Unit) {
                            detectDragGestures { change, dragAmount ->
                                change.consume()
                                onDrag?.invoke(dragAmount.x, dragAmount.y)
                            }
                        },
                    contentAlignment = Alignment.Center
                ) {
                    Text("══ DRAG ══", color = Color.LightGray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }
            }
            
            // Header with Overlay Controls (Sticky)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = if (isMinimized) 8.dp else 16.dp)
                    .padding(bottom = 8.dp), 
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = if (isMinimized) "DN" else "DraftNexus AI",
                    fontSize = if (isMinimized) 14.sp else 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    // Overlay Controls: Shrink/Expand + Close
                    if (isOverlay) {
                        // Shrink/Expand Toggle
                        Button(
                            onClick = { isMinimized = !isMinimized },
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF03DAC5)),
                            contentPadding = PaddingValues(4.dp),
                            modifier = Modifier.size(36.dp)
                        ) {
                            Icon(
                                imageVector = if (isMinimized) Icons.Default.KeyboardArrowDown else Icons.Default.KeyboardArrowUp,
                                contentDescription = if (isMinimized) "Expand" else "Minimize",
                                modifier = Modifier.size(20.dp)
                            )
                        }
                        
                        // Close Button
                        Button(
                            onClick = { onCloseOverlay?.invoke() },
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFCF6679)),
                            contentPadding = PaddingValues(4.dp),
                            modifier = Modifier.size(36.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Close,
                                contentDescription = "Close",
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    }
                    
                    // Clear Button (always visible)
                    Button(
                        onClick = { 
                            viewModel.clearDraft()
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFCF6679)),
                        contentPadding = PaddingValues(4.dp),
                        modifier = Modifier.size(36.dp)
                    ) {
                        Text("Clear", fontSize = 10.sp)
                    }
                }
            }

            Box(modifier = Modifier.weight(1f)) {
                LazyColumn(
                    modifier = Modifier.fillMaxSize()
                        .padding(horizontal = if (isMinimized) 8.dp else 16.dp)
                        .padding(bottom = if (isMinimized) 8.dp else 16.dp)
                ) {
            
            item {
                Spacer(modifier = Modifier.height(if (isMinimized) 4.dp else 16.dp))
                if (!isMinimized) {
                    Text("Debug: ${state.debugText}", color = Color.Yellow, fontSize = 10.sp, modifier = Modifier.padding(top = 4.dp))
                }
            }
            
            // Content (hidden when minimized)
            if (!isMinimized) {
                item {
                    // Enemy Team
                    Text("Enemy Team", color = Color(0xFFF44336), fontWeight = FontWeight.Bold)
                    TeamRow(
                        heroes = state.enemies,
                        isAlly = false,
                        onSlotClick = { idx ->
                            selectionMode = SelectionMode(false, idx)
                            showHeroSelector = true
                        }
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                }

                item {
                    // Ally Team
                    Text("Allied Team", color = Color(0xFF4CAF50), fontWeight = FontWeight.Bold)
                    TeamRow(
                        heroes = state.allies,
                        isAlly = true,
                        onSlotClick = { idx ->
                            selectionMode = SelectionMode(true, idx)
                            showHeroSelector = true
                        }
                    )
                    Spacer(modifier = Modifier.height(24.dp))
                }

                item {
                     Text("Recommendations", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                     Spacer(modifier = Modifier.height(8.dp))
                }

                if (state.recommendations.isEmpty()) {
                    item {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(100.dp)
                                .background(Color(0xFF262730), RoundedCornerShape(8.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            Text("Select heroes to get suggestions", color = Color.Gray)
                        }
                    }
                } else {
                    val lanes = listOf("Exp", "Jungle", "Mid", "Gold", "Roam")
                    items(lanes) { lane ->
                        val recs = state.recommendations[lane]
                        if (!recs.isNullOrEmpty()) {
                            Text(
                                text = lane, 
                                color = Color.White, 
                                fontSize = 13.sp, 
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(vertical = 2.dp)
                            )
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                 val recsToShow = recs.take(3)
                                 recsToShow.forEach { rec ->
                                     RecommendationCard(
                                         rec = rec,
                                         modifier = Modifier.weight(1f),
                                         onClick = {
                                             val emptySlot = state.allies.indexOfFirst { it == null }
                                             if (emptySlot != -1) {
                                                 viewModel.selectAlly(emptySlot, rec.hero)
                                             }
                                         }
                                     )
                                 }
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                        }
                    }
                }
            } // End isMinimized Block
            } // End LazyColumn

                // Show Selector INSIDE the content area (below header)
                if (showHeroSelector && selectionMode != null) {
                    HeroSelectorDialog(
                        heroes = state.heroes,
                        isOverlay = isOverlay,
                        selectedTabIndex = selectorTabIndex,
                        onTabSelected = { selectorTabIndex = it },
                        lazyGridState = selectorScrollState,
                        onDismiss = { showHeroSelector = false },
                        onHeroSelected = { hero ->
                            val mode = selectionMode!!
                            if (mode.isAlly) {
                                viewModel.selectAlly(mode.index, hero)
                            } else {
                                viewModel.selectEnemy(mode.index, hero)
                            }
                            showHeroSelector = false
                        }
                    )
                }
            } // End Box wrapping LazyColumn and HeroSelector
        
        // Snackbar Host
        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier.align(Alignment.BottomCenter)
        )
        
        // Show Selector

    }
}

@Composable
fun TeamRow(heroes: List<Hero?>, isAlly: Boolean, onSlotClick: (Int) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        for (i in 0 until 5) {
            val hero = heroes.getOrNull(i)
            HeroSlot(hero, onClick = { onSlotClick(i) }, modifier = Modifier.weight(1f))
        }
    }
}

@Composable
fun HeroSlot(hero: Hero?, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(1f)
                .shadow(
                    elevation = if (hero != null) 8.dp else 2.dp,
                    shape = CircleShape,
                    spotColor = if (hero != null) Color(0xFF6200EE) else Color.Transparent
                )
                .clip(CircleShape)
                .background(
                    if (hero != null) 
                        Brush.radialGradient(listOf(Color(0xFF404040), Color(0xFF262626)))
                    else 
                        Brush.radialGradient(listOf(Color(0xFF333333), Color(0xFF1A1A1A)))
                )
                .border(
                    width = 2.dp, 
                    brush = if (hero != null) 
                        Brush.linearGradient(listOf(Color(0xFFBB86FC), Color(0xFF6200EE)))
                    else 
                        Brush.linearGradient(listOf(Color.DarkGray, Color.DarkGray)),
                    shape = CircleShape
                )
                .clickable { onClick() },
            contentAlignment = Alignment.Center
        ) {
            if (hero != null) {
                AsyncImage(
                    model = hero.iconUrl,
                    contentDescription = hero.name,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                Text("+", color = Color.Gray, fontSize = 20.sp)
            }
        }
        Text(
            text = hero?.name ?: "Empty",
            fontSize = 9.sp,
            color = if (hero != null) Color.White else Color.Gray,
            fontWeight = if (hero != null) FontWeight.Medium else FontWeight.Normal,
            maxLines = 1,
            modifier = Modifier.padding(top = 2.dp)
        )
    }
}

@Composable
fun RecommendationCard(rec: Recommendation, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val scoreColor = when {
        rec.score >= 0.8f -> Color(0xFF4CAF50) // Green
        rec.score >= 0.6f -> Color(0xFFFFC107) // Yellow  
        else -> Color(0xFFFF9800) // Orange
    }
    
    Column(
        modifier = modifier
            .shadow(elevation = 2.dp, shape = RoundedCornerShape(8.dp))
            .background(
                Brush.verticalGradient(
                    listOf(Color(0xFF2D2D3A), Color(0xFF1E1E26))
                ),
                RoundedCornerShape(8.dp)
            )
            .border(
                width = 1.dp,
                brush = Brush.linearGradient(
                    listOf(scoreColor.copy(alpha = 0.5f), scoreColor.copy(alpha = 0.3f))
                ),
                shape = RoundedCornerShape(8.dp)
            )
            .clickable { onClick() }
            .padding(6.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .clip(CircleShape)
                .border(
                    width = 2.dp,
                    color = scoreColor,
                    shape = CircleShape
                )
        ) {
            AsyncImage(
                model = rec.hero.iconUrl,
                contentDescription = rec.hero.name,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = rec.hero.name, 
            fontWeight = FontWeight.Bold, 
            fontSize = 10.sp, 
            maxLines = 1,
            color = Color.White
        )
        Text(
            text = "${(rec.score * 100).toInt()}%",
            color = scoreColor,
            fontWeight = FontWeight.Bold,
            fontSize = 10.sp
        )
    }
} 

@Composable
fun HeroSelectorDialog(
    heroes: List<Hero>,
    isOverlay: Boolean,
    selectedTabIndex: Int,
    onTabSelected: (Int) -> Unit,
    lazyGridState: androidx.compose.foundation.lazy.grid.LazyGridState,
    onDismiss: () -> Unit,
    onHeroSelected: (Hero?) -> Unit
) {
    val tabs = listOf("All", "Exp", "Mid", "Roam", "Jungle", "Gold")
    val laneIds = listOf(0, 1, 2, 3, 4, 5)

    val filteredHeroes = remember(selectedTabIndex, heroes) {
        val targetLane = laneIds[selectedTabIndex]
        if (targetLane == 0) heroes.sortedBy { it.name }
        else heroes.filter { it.primaryLane == targetLane }.sortedBy { it.name }
    }

    val configuration = LocalConfiguration.current
    val isLandscape = configuration.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE

    val content = @Composable { modifier: Modifier ->
        Column(
            modifier = modifier.padding(8.dp)
        ) {
            ScrollableTabRow(
                selectedTabIndex = selectedTabIndex,
                containerColor = Color.Transparent,
                contentColor = Color(0xFFBB86FC),
                edgePadding = 0.dp
            ) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTabIndex == index,
                        onClick = { onTabSelected(index) },
                        text = { Text(title, fontSize = 12.sp) }
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(if (isLandscape) 4.dp else 8.dp))

            LazyVerticalGrid(
                state = lazyGridState,
                columns = if (isOverlay && isLandscape) GridCells.Fixed(3) else GridCells.Fixed(5),
                verticalArrangement = Arrangement.spacedBy(4.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                modifier = if (isOverlay) Modifier.weight(1f) else Modifier.height(500.dp)
            ) {
                items(filteredHeroes) { hero ->
                    val iconSize = 48.dp
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier
                            .clickable { onHeroSelected(hero) }
                            .padding(4.dp)
                    ) {
                        AsyncImage(
                            model = hero.iconUrl,
                            contentDescription = hero.name,
                            modifier = Modifier
                                .size(iconSize)
                                .clip(CircleShape)
                                .background(Color.Gray),
                            contentScale = ContentScale.Crop
                        )
                        Text(hero.name, fontSize = 9.sp, maxLines = 1, textAlign = TextAlign.Center, color = Color.White)
                    }
                }
            }
            
            // Custom Buttons Row
            Row(
                 modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                 horizontalArrangement = Arrangement.SpaceBetween
            ) {
                TextButton(
                    onClick = { onHeroSelected(null) },
                    colors = ButtonDefaults.textButtonColors(contentColor = Color(0xFFCF6679))
                ) {
                    Text("Remove")
                }
                
                TextButton(onClick = onDismiss) {
                    Text("Cancel")
                }
            }
        }
    }

    if (isOverlay) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.5f))
                .clickable { onDismiss() },
            contentAlignment = Alignment.Center
        ) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth(0.95f)
                    .fillMaxSize() // Fill the 400dp window provided by Service
                    .border(1.dp, Color.Gray, RoundedCornerShape(16.dp))
                    .clickable(enabled = false) {}, // Consume clicks
                shape = RoundedCornerShape(16.dp),
                color = Color(0xFF333333)
            ) {
                Column(modifier = Modifier.fillMaxSize()) {
                    val headerPadding = if (isLandscape) 4.dp else 16.dp
                    Text("Select Hero", color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(headerPadding))
                    content(Modifier.weight(1f))
                }
            }
        }
    } else {
        AlertDialog(
            onDismissRequest = onDismiss,
            title = { Text("Select Hero", color = Color.White) }, 
            text = { content(Modifier) },
            confirmButton = {}, 
            dismissButton = {}, 
            containerColor = Color(0xFF333333)
        )
    }
}

data class SelectionMode(val isAlly: Boolean, val index: Int)

package com.draftnexus.ai.core.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.draftnexus.ai.core.model.*

@Composable
fun DraftScreen(
    state: DraftState,
    onAllySelected: (Int, Hero?) -> Unit,
    onEnemySelected: (Int, Hero?) -> Unit,
    onClearDraft: () -> Unit,
    isOverlay: Boolean = false,
    onCloseOverlay: (() -> Unit)? = null,
    onDrag: ((Float, Float) -> Unit)? = null, // dx, dy delta
    onMinimizedChange: ((Boolean) -> Unit)? = null, // notify when minimized state changes
    onHeroSelectorVisibilityChange: ((Boolean) -> Unit)? = null // notify when hero selector opens/closes
) {
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

    Box(modifier = if (isMinimized) Modifier.wrapContentSize() else Modifier.fillMaxSize()) {
        if (isMinimized) {
            // Minimized FAB State
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(Color(0xFF3EA6FF)) // YouTube Action Blue
                    .clickable { isMinimized = false }
                    .pointerInput(Unit) {
                        detectDragGestures { change, dragAmount ->
                            change.consume()
                            onDrag?.invoke(dragAmount.x, dragAmount.y)
                        }
                    },
                contentAlignment = Alignment.Center
            ) {
                // DraftNexus / AI Icon
                Text("DN", color = Color(0xFF0F0F0F), fontWeight = FontWeight.Bold, fontSize = 20.sp)
            }
        } else {
            // Expanded State
            Column(modifier = Modifier.fillMaxSize()) {
                // Drag Bar (outside LazyColumn to prevent scroll conflict)
            if (isOverlay) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp)
                        .padding(top = 16.dp)
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
                    .padding(horizontal = 16.dp)
                    .padding(vertical = 12.dp), 
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "DraftNexus AI",
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFFF1F1F1) // YouTube White
                )
                
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    // Overlay Controls: Shrink/Expand + Close
                    if (isOverlay) {
                        // Shrink Toggle
                        IconButton(
                            onClick = { isMinimized = true },
                            modifier = Modifier.size(36.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.KeyboardArrowDown,
                                contentDescription = "Minimize",
                                tint = Color(0xFFF1F1F1)
                            )
                        }
                        
                        // Close Button
                        IconButton(
                            onClick = { onCloseOverlay?.invoke() },
                            modifier = Modifier.size(36.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Close,
                                contentDescription = "Close",
                                tint = Color(0xFFF1F1F1)
                            )
                        }
                    }
                    
                    // Clear Button (always visible)
                    TextButton(
                        onClick = { onClearDraft() },
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                        modifier = Modifier.height(36.dp),
                        shape = RoundedCornerShape(18.dp)
                    ) {
                        Text("Clear", fontSize = 14.sp, fontWeight = FontWeight.Medium, color = Color(0xFF3EA6FF)) // YouTube Action Blue
                    }
                }
            }

            Box(modifier = Modifier.weight(1f)) {
                LazyColumn(
                    modifier = Modifier.fillMaxSize()
                        .padding(horizontal = 16.dp)
                        .padding(bottom = 16.dp)
                ) {
            
            item {
                Spacer(modifier = Modifier.height(16.dp))
                Text("Debug: ${state.debugText}", color = Color.Yellow, fontSize = 10.sp, modifier = Modifier.padding(top = 4.dp))
            }
            
            // Content
            item {
                    // Enemy Team
                    Text("Enemy Team", color = Color(0xFFAAAAAA), fontSize = 14.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(bottom = 8.dp))
                    TeamRow(
                        heroes = state.enemies,
                        isAlly = false,
                        onSlotClick = { idx ->
                            selectionMode = SelectionMode(false, idx)
                            showHeroSelector = true
                        }
                    )
                    Spacer(modifier = Modifier.height(24.dp))
                }

                item {
                    // Ally Team
                    Text("Allied Team", color = Color(0xFFAAAAAA), fontSize = 14.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(bottom = 8.dp))
                    TeamRow(
                        heroes = state.allies,
                        isAlly = true,
                        onSlotClick = { idx ->
                            selectionMode = SelectionMode(true, idx)
                            showHeroSelector = true
                        }
                    )
                    Spacer(modifier = Modifier.height(32.dp))
                }

                item {
                     Text("Recommendations", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color(0xFFF1F1F1))
                     Spacer(modifier = Modifier.height(12.dp))
                }

                if (state.recommendations.isEmpty()) {
                    item {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(100.dp)
                                .background(Color(0xFF212121), RoundedCornerShape(12.dp)), // YouTube Surface Gray
                            contentAlignment = Alignment.Center
                        ) {
                            Text("Select heroes to get suggestions", color = Color(0xFFAAAAAA), fontSize = 14.sp)
                        }
                    }
                } else {
                    val lanes = listOf("Exp", "Jungle", "Mid", "Gold", "Roam")
                    items(lanes) { lane ->
                        val recs = state.recommendations[lane]
                        if (!recs.isNullOrEmpty()) {
                            Text(
                                text = lane, 
                                color = Color(0xFFF1F1F1), 
                                fontSize = 14.sp, 
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(vertical = 8.dp)
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
                                                 onAllySelected(emptySlot, rec.hero)
                                             }
                                         }
                                     )
                                 }
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                        }
                    }
                }
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
                                onAllySelected(mode.index, hero)
                            } else {
                                onEnemySelected(mode.index, hero)
                            }
                            showHeroSelector = false
                        }
                    )
                }
            } // End Box wrapping LazyColumn and HeroSelector
        } // End Column or Box for Expanded view
        } // End isMinimized else block
        
        // Snackbar Host
        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier.align(Alignment.BottomCenter)
        )
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
                .aspectRatio(0.75f) // YouTube Shorts aspect ratio (vertical)
                .clip(RoundedCornerShape(8.dp))
                .background(if (hero != null) Color(0xFF212121) else Color(0xFF272727)) // Subtle dark backgrounds
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
                Text("+", color = Color(0xFFAAAAAA), fontSize = 24.sp, fontWeight = FontWeight.Light)
            }
        }
        Text(
            text = hero?.name ?: "Empty",
            fontSize = 11.sp,
            color = if (hero != null) Color(0xFFF1F1F1) else Color(0xFFAAAAAA),
            fontWeight = if (hero != null) FontWeight.Medium else FontWeight.Normal,
            maxLines = 1,
            modifier = Modifier.padding(top = 6.dp)
        )
    }
}

@Composable
fun RecommendationCard(rec: Recommendation, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val scoreColor = when {
        rec.score >= 0.8f -> Color(0xFF2BA640) // Subdued Green
        rec.score >= 0.6f -> Color(0xFFD4B237) // Subdued Yellow  
        else -> Color(0xFFC45E3B) // Subdued Orange
    }
    
    Column(
        modifier = modifier
            .background(Color(0xFF212121), RoundedCornerShape(12.dp)) // YouTube Surface Gray
            .clip(RoundedCornerShape(12.dp))
            .clickable { onClick() }
            .padding(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(1f)
                .clip(RoundedCornerShape(8.dp))
        ) {
            AsyncImage(
                model = rec.hero.iconUrl,
                contentDescription = rec.hero.name,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = rec.hero.name, 
            fontWeight = FontWeight.Medium, 
            fontSize = 12.sp, 
            maxLines = 1,
            color = Color(0xFFF1F1F1) // YouTube White
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = "${(rec.score * 100).toInt()}% Match",
            color = scoreColor,
            fontWeight = FontWeight.Normal,
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
            modifier = modifier.padding(horizontal = 0.dp, vertical = 8.dp)
        ) {
            // YouTube-style Chips for Tabs
            LazyRow(
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(tabs.size) { index ->
                    val isSelected = selectedTabIndex == index
                    Box(
                        modifier = Modifier
                            .background(
                                color = if (isSelected) Color(0xFFF1F1F1) else Color(0xFF272727),
                                shape = RoundedCornerShape(16.dp)
                            )
                            .clickable { onTabSelected(index) }
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                    ) {
                        Text(
                            text = tabs[index],
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium,
                            color = if (isSelected) Color(0xFF0F0F0F) else Color(0xFFF1F1F1)
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(if (isLandscape) 8.dp else 16.dp))

            LazyVerticalGrid(
                state = lazyGridState,
                columns = if (isOverlay && isLandscape) GridCells.Fixed(3) else GridCells.Fixed(4),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = if (isOverlay) Modifier.weight(1f) else Modifier.height(500.dp)
            ) {
                items(filteredHeroes, key = { it.id }) { hero ->
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier
                            .clickable { onHeroSelected(hero) }
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .aspectRatio(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0xFF272727))
                        ) {
                            AsyncImage(
                                model = hero.iconUrl,
                                contentDescription = hero.name,
                                modifier = Modifier.fillMaxSize(),
                                contentScale = ContentScale.Crop
                            )
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = hero.name, 
                            fontSize = 11.sp, 
                            maxLines = 1, 
                            textAlign = TextAlign.Center, 
                            color = Color(0xFFF1F1F1),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }
            
            // Custom Buttons Row
            Row(
                 modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                 horizontalArrangement = Arrangement.SpaceBetween
            ) {
                TextButton(
                    onClick = { onHeroSelected(null) }
                ) {
                    Text("Remove", color = Color(0xFFCF6679))
                }
                
                TextButton(onClick = onDismiss) {
                    Text("Cancel", color = Color(0xFFF1F1F1))
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
                    .fillMaxWidth()
                    .fillMaxHeight(0.8f) // Dialog occupies 80% height in overlay
                    .align(Alignment.BottomCenter) // Snap to bottom like YouTube sheets
                    .clickable(enabled = false) {}, // Consume clicks
                shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp), // Rounded top only
                color = Color(0xFF212121) // YouTube Surface Gray
            ) {
                Column(modifier = Modifier.fillMaxSize()) {
                    // Drag handle aesthetic
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 12.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Box(
                            modifier = Modifier
                                .width(40.dp)
                                .height(4.dp)
                                .background(Color(0xFF555555), RoundedCornerShape(2.dp))
                        )
                    }
                    Text(
                        "Select Hero", 
                        color = Color(0xFFF1F1F1), 
                        fontSize = 18.sp, 
                        fontWeight = FontWeight.Bold, 
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
                    )
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

/**
 * SentinelTwin AI — 3D Digital Twin Engine
 * Full Three.js 3D factory environment with:
 * - 5 interactive machines (clickable, color-coded by health)
 * - Animated conveyor belts with moving products
 * - Robotic arms with pick-and-place animation
 * - Forklifts traversing the factory floor
 * - Health heatmap overlay
 * - Pipeline color changes by machine status
 * - Fault visual effects: vibration shake, spark particles, warning lights
 * - Orbit controls for camera rotation, zoom, pan
 */

class DigitalTwin3D {
  constructor(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.clock = null;
    this.machineObjects = {};
    this.conveyorBelts = [];
    this.conveyorItems = [];
    this.pipes = [];
    this.pipeMaterials = {};
    this.robotArms = [];
    this.forklifts = [];
    this.warningLights = [];
    this.sparkSystems = [];
    this.heatmapPlanes = {};
    this.machineStates = {};
    this.animFrameId = null;
    this.selectedMachine = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.heatmapVisible = true;
    this.pipelinesVisible = true;
    this._initialized = false;
    this._conveyorOffset = 0;

    // Machine positions in 3D space (factory floor layout)
    this.machinePositions = {
      M1: new THREE.Vector3(-16, 0, 0),
      M2: new THREE.Vector3(-8,  0, 0),
      M3: new THREE.Vector3(  0, 0, 0),
      M4: new THREE.Vector3(  8, 0, 0),
      M5: new THREE.Vector3( 16, 0, 0),
    };

    this.machineColors = {
      normal:  0x2196F3,
      warning: 0xFF9800,
      critical:0xF44336,
      failure: 0x9C27B0,
      healing: 0x4CAF50,
      offline: 0x607D8B,
    };

    this.pipeColors = {
      normal:  0x2196F3,
      warning: 0xFF9800,
      critical:0xF44336,
      failure: 0xE53935,
      healing: 0x4CAF50,
      offline: 0x607D8B,
    };
  }

  init() {
    if (this._initialized) return;
    if (!this.container) return;
    this._initialized = true;

    this.clock = new THREE.Clock();

    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xF0F4FF);
    this.scene.fog = new THREE.Fog(0xF0F4FF, 60, 120);

    // Camera
    const w = this.container.clientWidth || 800;
    const h = this.container.clientHeight || 500;
    this.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 500);
    this.camera.position.set(0, 28, 40);
    this.camera.lookAt(0, 0, 0);

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setSize(w, h);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.container.appendChild(this.renderer.domElement);

    // Orbit Controls (manual implementation — no import needed)
    this._setupOrbitControls();

    // Lighting
    this._setupLighting();

    // Environment
    this._buildFactory();

    // Events
    window.addEventListener('resize', () => this._onResize());
    this.renderer.domElement.addEventListener('click', (e) => this._onCanvasClick(e));

    // Start render loop
    this._animate();
  }

  _setupOrbitControls() {
    // Minimal orbit controls implementation
    const el = this.renderer.domElement;
    let isDown = false, prevX = 0, prevY = 0;
    let spherical = { theta: 0, phi: Math.PI / 4, radius: 50 };
    let panTarget = new THREE.Vector3(0, 2, 0);

    const updateCamera = () => {
      const x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta) + panTarget.x;
      const y = spherical.radius * Math.cos(spherical.phi) + panTarget.y;
      const z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta) + panTarget.z;
      this.camera.position.set(x, y, z);
      this.camera.lookAt(panTarget);
    };

    el.addEventListener('mousedown', (e) => {
      isDown = true; prevX = e.clientX; prevY = e.clientY;
    });
    window.addEventListener('mouseup', () => { isDown = false; });
    el.addEventListener('mousemove', (e) => {
      if (!isDown) return;
      const dx = (e.clientX - prevX) * 0.008;
      const dy = (e.clientY - prevY) * 0.008;
      prevX = e.clientX; prevY = e.clientY;
      if (e.buttons === 1) {
        spherical.theta -= dx;
        spherical.phi = Math.max(0.15, Math.min(Math.PI / 2.1, spherical.phi + dy));
      } else if (e.buttons === 2) {
        const right = new THREE.Vector3().crossVectors(
          new THREE.Vector3(0,1,0),
          this.camera.position.clone().sub(panTarget).normalize()
        ).normalize();
        panTarget.addScaledVector(right, dx * spherical.radius * 0.5);
        panTarget.y -= dy * spherical.radius * 0.4;
      }
      updateCamera();
    });
    el.addEventListener('wheel', (e) => {
      spherical.radius = Math.max(10, Math.min(90, spherical.radius + e.deltaY * 0.05));
      updateCamera();
      e.preventDefault();
    }, { passive: false });
    el.addEventListener('contextmenu', (e) => e.preventDefault());

    updateCamera();
    this._orbitState = { spherical, panTarget, updateCamera };
  }

  _setupLighting() {
    const ambient = new THREE.AmbientLight(0xFFFFFF, 0.7);
    this.scene.add(ambient);

    const sun = new THREE.DirectionalLight(0xFFFFFF, 0.9);
    sun.position.set(20, 40, 20);
    sun.castShadow = true;
    sun.shadow.camera.left = -40;
    sun.shadow.camera.right = 40;
    sun.shadow.camera.top = 30;
    sun.shadow.camera.bottom = -30;
    sun.shadow.mapSize.width = 2048;
    sun.shadow.mapSize.height = 2048;
    sun.shadow.bias = -0.001;
    this.scene.add(sun);

    const fill = new THREE.DirectionalLight(0xE8F4FF, 0.4);
    fill.position.set(-15, 20, -10);
    this.scene.add(fill);

    // Ceiling point lights above each machine
    const machinePositions = Object.values(this.machinePositions);
    machinePositions.forEach((pos) => {
      const light = new THREE.PointLight(0xFFFFCC, 0.4, 18);
      light.position.set(pos.x, 10, pos.z);
      this.scene.add(light);
    });
  }

  _buildFactory() {
    this._buildFloor();
    this._buildWalls();
    this._buildCeiling();
    this._buildColumns();
    this._buildMachines();
    this._buildConveyorBelts();
    this._buildPipelines();
    this._buildRoboticArms();
    this._buildForklifts();
    this._buildHeatmapOverlay();
    this._buildFloorGrid();
  }

  _buildFloor() {
    const geo = new THREE.PlaneGeometry(80, 50);
    const mat = new THREE.MeshLambertMaterial({ color: 0xF5F5F5 });
    const floor = new THREE.Mesh(geo, mat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);

    // Floor tiles pattern
    const tileGeo = new THREE.PlaneGeometry(78, 48);
    const tileCanvas = document.createElement('canvas');
    tileCanvas.width = 512; tileCanvas.height = 512;
    const ctx = tileCanvas.getContext('2d');
    ctx.fillStyle = '#F8F8F8';
    ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = '#E0E0E0';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 8; i++) {
      ctx.beginPath(); ctx.moveTo(i * 64, 0); ctx.lineTo(i * 64, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i * 64); ctx.lineTo(512, i * 64); ctx.stroke();
    }
    const tileTex = new THREE.CanvasTexture(tileCanvas);
    tileTex.wrapS = tileTex.wrapT = THREE.RepeatWrapping;
    tileTex.repeat.set(8, 5);
    const tileMat = new THREE.MeshLambertMaterial({ map: tileTex, transparent: true, opacity: 0.6 });
    const tiles = new THREE.Mesh(tileGeo, tileMat);
    tiles.rotation.x = -Math.PI / 2;
    tiles.position.y = 0.01;
    this.scene.add(tiles);
  }

  _buildFloorGrid() {
    const gridHelper = new THREE.GridHelper(80, 40, 0xCCCCCC, 0xDDDDDD);
    gridHelper.position.y = 0.02;
    gridHelper.material.opacity = 0.3;
    gridHelper.material.transparent = true;
    this.scene.add(gridHelper);
  }

  _buildWalls() {
    const wallMat = new THREE.MeshLambertMaterial({ color: 0xEAEEF5, side: THREE.DoubleSide });
    // Back wall
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(80, 20), wallMat);
    backWall.position.set(0, 10, -25);
    this.scene.add(backWall);
    // Side walls
    const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(50, 20), wallMat);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.position.set(-40, 10, 0);
    this.scene.add(leftWall);
    const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(50, 20), wallMat);
    rightWall.rotation.y = -Math.PI / 2;
    rightWall.position.set(40, 10, 0);
    this.scene.add(rightWall);
  }

  _buildCeiling() {
    const ceilGeo = new THREE.PlaneGeometry(80, 50);
    const ceilMat = new THREE.MeshLambertMaterial({ color: 0xEEEEEE, side: THREE.DoubleSide });
    const ceil = new THREE.Mesh(ceilGeo, ceilMat);
    ceil.rotation.x = Math.PI / 2;
    ceil.position.y = 20;
    this.scene.add(ceil);

    // Roof trusses
    for (let x = -30; x <= 30; x += 15) {
      const tGeo = new THREE.BoxGeometry(0.4, 2, 40);
      const tMat = new THREE.MeshLambertMaterial({ color: 0x90A4AE });
      const truss = new THREE.Mesh(tGeo, tMat);
      truss.position.set(x, 19, 0);
      this.scene.add(truss);
    }
  }

  _buildColumns() {
    const colMat = new THREE.MeshLambertMaterial({ color: 0x90A4AE });
    const positions = [[-38, 0, -22], [38, 0, -22], [-38, 0, 22], [38, 0, 22]];
    positions.forEach(([x, y, z]) => {
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 20, 8), colMat);
      col.position.set(x, 10, z);
      this.scene.add(col);
    });
  }

  _buildMachines() {
    const machineConfigs = {
      M1: { color: 0x1565C0, h: 4.5, w: 3.5, d: 3.5, label: 'M1\nProcessor' },
      M2: { color: 0x0288D1, h: 5.5, w: 3.0, d: 3.0, label: 'M2\nAssembly Robot' },
      M3: { color: 0x00796B, h: 3.5, w: 4.0, d: 3.5, label: 'M3\nQuality' },
      M4: { color: 0x558B2F, h: 4.0, w: 3.5, d: 3.5, label: 'M4\nPackaging' },
      M5: { color: 0x6A1B9A, h: 5.0, w: 3.0, d: 3.0, label: 'M5\nDistrib. Robot' },
    };

    Object.entries(machineConfigs).forEach(([id, cfg]) => {
      const group = new THREE.Group();
      const pos = this.machinePositions[id];
      group.position.copy(pos);

      // Machine base platform
      const baseMat = new THREE.MeshLambertMaterial({ color: 0x455A64 });
      const base = new THREE.Mesh(new THREE.BoxGeometry(cfg.w + 0.5, 0.4, cfg.d + 0.5), baseMat);
      base.position.y = 0.2;
      base.castShadow = true;
      base.receiveShadow = true;
      group.add(base);

      // Main machine body
      const bodyMat = new THREE.MeshLambertMaterial({ color: cfg.color });
      const body = new THREE.Mesh(new THREE.BoxGeometry(cfg.w, cfg.h, cfg.d), bodyMat);
      body.position.y = cfg.h / 2 + 0.4;
      body.castShadow = true;
      body.receiveShadow = true;
      group.add(body);

      // Panel face (front detail)
      const panelMat = new THREE.MeshLambertMaterial({ color: 0xECEFF1 });
      const panel = new THREE.Mesh(new THREE.BoxGeometry(cfg.w * 0.7, cfg.h * 0.5, 0.15), panelMat);
      panel.position.set(0, cfg.h / 2 + 0.4, cfg.d / 2 + 0.05);
      group.add(panel);

      // Status light (top of machine)
      const lightGeo = new THREE.SphereGeometry(0.25, 12, 12);
      const lightMat = new THREE.MeshLambertMaterial({ color: 0x4CAF50, emissive: 0x4CAF50, emissiveIntensity: 0.5 });
      const statusLight = new THREE.Mesh(lightGeo, lightMat);
      statusLight.position.y = cfg.h + 0.7;
      group.add(statusLight);

      // Warning light ring
      const warnLightMat = new THREE.MeshLambertMaterial({ color: 0xFF9800, emissive: 0xFF9800, emissiveIntensity: 0 });
      const warnLight = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.08, 8, 16), warnLightMat);
      warnLight.position.y = cfg.h + 0.5;
      group.add(warnLight);

      // Machine label sprite
      const labelSprite = this._createTextSprite(id, cfg.color);
      labelSprite.position.y = cfg.h + 1.6;
      labelSprite.scale.set(3, 1.2, 1);
      group.add(labelSprite);

      // Heatmap overlay plane (health color)
      const hmGeo = new THREE.PlaneGeometry(cfg.w + 1, cfg.d + 1);
      const hmMat = new THREE.MeshBasicMaterial({
        color: 0x4CAF50,
        transparent: true,
        opacity: 0.18,
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      const hmPlane = new THREE.Mesh(hmGeo, hmMat);
      hmPlane.rotation.x = -Math.PI / 2;
      hmPlane.position.y = 0.05;
      group.add(hmPlane);

      this.scene.add(group);

      this.machineObjects[id] = {
        group,
        body,
        bodyMat,
        statusLight,
        statusLightMat: lightMat,
        warnLight,
        warnLightMat,
        hmPlane,
        hmMat,
        cfg,
        originalPos: pos.clone(),
        shakePhase: Math.random() * Math.PI * 2,
        sparks: null,
      };

      // Make machine clickable — store ID on group
      group.userData.machineId = id;
      body.userData.machineId = id;
    });
  }

  _createTextSprite(text, color) {
    const canvas = document.createElement('canvas');
    canvas.width = 256; canvas.height = 80;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = `#${color.toString(16).padStart(6,'0')}CC`;
    ctx.roundRect(4, 4, 248, 72, 12);
    ctx.fill();
    ctx.fillStyle = 'white';
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 128, 40);
    const texture = new THREE.CanvasTexture(canvas);
    const mat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    return new THREE.Sprite(mat);
  }

  _buildConveyorBelts() {
    const beltMat = new THREE.MeshLambertMaterial({ color: 0x37474F });
    const rollerMat = new THREE.MeshLambertMaterial({ color: 0x78909C });
    const beltConnections = [
      { from: 'M1', to: 'M2' }, { from: 'M2', to: 'M3' },
      { from: 'M3', to: 'M4' }, { from: 'M4', to: 'M5' },
    ];

    beltConnections.forEach(({ from, to }, idx) => {
      const fromPos = this.machinePositions[from];
      const toPos = this.machinePositions[to];
      const midX = (fromPos.x + toPos.x) / 2;
      const length = Math.abs(toPos.x - fromPos.x) - 3.8;

      // Belt frame
      const frameGeo = new THREE.BoxGeometry(length, 0.25, 1.2);
      const belt = new THREE.Mesh(frameGeo, beltMat);
      belt.position.set(midX, 1.6, 0);
      belt.receiveShadow = true;
      this.scene.add(belt);

      // Belt texture (moving stripes)
      const beltCanvas = document.createElement('canvas');
      beltCanvas.width = 256; beltCanvas.height = 64;
      const ctx = beltCanvas.getContext('2d');
      ctx.fillStyle = '#263238';
      ctx.fillRect(0, 0, 256, 64);
      for (let i = 0; i < 256; i += 16) {
        ctx.fillStyle = '#37474F';
        ctx.fillRect(i, 0, 8, 64);
      }
      const beltTex = new THREE.CanvasTexture(beltCanvas);
      beltTex.wrapS = THREE.RepeatWrapping;
      beltTex.repeat.set(length / 2, 1);
      const topMat = new THREE.MeshLambertMaterial({ map: beltTex });
      const top = new THREE.Mesh(new THREE.PlaneGeometry(length, 1.0), topMat);
      top.rotation.x = -Math.PI / 2;
      top.position.set(midX, 1.73, 0);
      this.scene.add(top);

      // Rollers
      for (let rx = fromPos.x + 2.2; rx < toPos.x - 2.0; rx += 1.5) {
        const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 1.3, 8), rollerMat);
        roller.rotation.z = Math.PI / 2;
        roller.position.set(rx, 1.5, 0);
        this.scene.add(roller);
      }

      // Store texture reference for animation
      this.conveyorBelts.push({ topMat, beltTex, belt, id: `CB${idx + 1}` });

      // Product items on belt
      const itemGeo = new THREE.BoxGeometry(0.6, 0.4, 0.6);
      const itemMat = new THREE.MeshLambertMaterial({ color: 0xFFC107 });
      const item = new THREE.Mesh(itemGeo, itemMat);
      item.position.set(fromPos.x + 2.5, 1.95, 0);
      item.castShadow = true;
      this.scene.add(item);
      this.conveyorItems.push({
        mesh: item,
        fromX: fromPos.x + 2.2,
        toX: toPos.x - 2.2,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.003,
      });
    });
  }

  _buildPipelines() {
    const pipePositions = [
      { from: 'M1', to: 'M2' }, { from: 'M2', to: 'M3' },
      { from: 'M3', to: 'M4' }, { from: 'M4', to: 'M5' },
    ];

    pipePositions.forEach(({ from, to }, idx) => {
      const fromPos = this.machinePositions[from];
      const toPos = this.machinePositions[to];
      const midX = (fromPos.x + toPos.x) / 2;
      const length = Math.abs(toPos.x - fromPos.x) - 3.5;

      const pipeMat = new THREE.MeshLambertMaterial({ color: 0x2196F3, emissive: 0x0D47A1, emissiveIntensity: 0.1 });
      const pipeGeo = new THREE.CylinderGeometry(0.15, 0.15, length, 10);
      const pipe = new THREE.Mesh(pipeGeo, pipeMat);
      pipe.rotation.z = Math.PI / 2;
      pipe.position.set(midX, 5.5, 1.2);
      this.scene.add(pipe);

      // Pipe connectors
      const connMat = new THREE.MeshLambertMaterial({ color: 0x37474F });
      [fromPos.x + 2.0, toPos.x - 2.0].forEach(cx => {
        const conn = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.3, 8), connMat);
        conn.rotation.z = Math.PI / 2;
        conn.position.set(cx, 5.5, 1.2);
        this.scene.add(conn);
      });

      this.pipes.push({ mesh: pipe, mat: pipeMat, fromMachine: from, toMachine: to });
      this.pipeMaterials[`${from}-${to}`] = pipeMat;
    });
  }

  _buildRoboticArms() {
    // M2 and M5 have robotic arms
    ['M2', 'M5'].forEach((machineId, idx) => {
      const pos = this.machinePositions[machineId].clone();
      const armGroup = new THREE.Group();
      armGroup.position.set(pos.x, 0, 2.5);

      const baseMat = new THREE.MeshLambertMaterial({ color: 0x455A64 });
      const jointMat = new THREE.MeshLambertMaterial({ color: 0xF57F17 });
      const armMat = new THREE.MeshLambertMaterial({ color: 0xECEFF1 });

      // Base
      const armBase = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.5, 0.5, 12), baseMat);
      armBase.position.y = 0.25;
      armGroup.add(armBase);

      // Lower arm
      const lowerArm = new THREE.Mesh(new THREE.BoxGeometry(0.25, 2.0, 0.25), armMat);
      lowerArm.position.y = 1.5;
      const lowerGroup = new THREE.Group();
      lowerGroup.position.y = 0.5;
      lowerGroup.add(lowerArm);

      // Upper arm
      const upperArm = new THREE.Mesh(new THREE.BoxGeometry(0.2, 1.8, 0.2), armMat);
      upperArm.position.y = 0.9;
      const upperGroup = new THREE.Group();
      upperGroup.position.y = 2.0;
      upperGroup.add(upperArm);

      // Joint spheres
      const joint1 = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 10), jointMat);
      joint1.position.y = 0.5;
      armGroup.add(joint1);
      lowerGroup.add(upperGroup);
      armGroup.add(lowerGroup);

      // Gripper
      const gripperMat = new THREE.MeshLambertMaterial({ color: 0x37474F });
      const gripper = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.2, 0.15), gripperMat);
      gripper.position.y = 1.8;
      upperGroup.add(gripper);

      this.scene.add(armGroup);
      this.robotArms.push({
        group: armGroup,
        lowerGroup,
        upperGroup,
        phase: idx * Math.PI,
        id: machineId,
      });
    });
  }

  _buildForklifts() {
    // Two forklifts patrolling the factory aisles
    for (let i = 0; i < 2; i++) {
      const group = new THREE.Group();
      const bodyMat = new THREE.MeshLambertMaterial({ color: i === 0 ? 0xF9A825 : 0x1565C0 });
      const darkMat = new THREE.MeshLambertMaterial({ color: 0x212121 });
      const body = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.2, 1.0), bodyMat);
      body.position.y = 0.7;
      group.add(body);
      const cabin = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.9, 0.9), bodyMat);
      cabin.position.set(0.2, 1.65, 0);
      group.add(cabin);
      const mast = new THREE.Mesh(new THREE.BoxGeometry(0.15, 2.5, 0.15), darkMat);
      mast.position.set(-0.7, 1.6, 0);
      group.add(mast);
      const fork1 = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.1, 0.2), darkMat);
      fork1.position.set(-0.7, 0.7, 0.3);
      group.add(fork1);
      const fork2 = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.1, 0.2), darkMat);
      fork2.position.set(-0.7, 0.7, -0.3);
      group.add(fork2);
      // Wheels
      const wheelMat = new THREE.MeshLambertMaterial({ color: 0x212121 });
      [[-0.6, 0.3, 0.55], [0.6, 0.3, 0.55], [-0.6, 0.3, -0.55], [0.6, 0.3, -0.55]].forEach(([x,y,z]) => {
        const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.2, 10), wheelMat);
        wheel.rotation.x = Math.PI / 2;
        wheel.position.set(x, y, z);
        group.add(wheel);
      });
      group.position.set(-20 + i * 5, 0, 8 + i * 4);
      this.scene.add(group);
      this.forklifts.push({
        group,
        startX: -24 + i * 6,
        endX: 24 - i * 6,
        speed: 0.02 + i * 0.01,
        progress: i * 0.5,
        zPos: 8 + i * 4,
      });
    }
  }

  _buildHeatmapOverlay() {
    // A subtle ground-level heatmap glow under each machine
    Object.entries(this.machinePositions).forEach(([id, pos]) => {
      const hmGeo = new THREE.CircleGeometry(3.5, 32);
      const hmMat = new THREE.MeshBasicMaterial({
        color: 0x4CAF50,
        transparent: true,
        opacity: 0.15,
        depthWrite: false,
      });
      const hm = new THREE.Mesh(hmGeo, hmMat);
      hm.rotation.x = -Math.PI / 2;
      hm.position.set(pos.x, 0.03, pos.z);
      this.scene.add(hm);
      this.heatmapPlanes[id] = { mesh: hm, mat: hmMat };
    });
  }

  _createSparkSystem(position) {
    const group = new THREE.Group();
    group.position.copy(position);
    group.position.y += 5;
    const particles = [];
    for (let i = 0; i < 20; i++) {
      const geo = new THREE.SphereGeometry(0.06, 4, 4);
      const mat = new THREE.MeshBasicMaterial({
        color: Math.random() > 0.5 ? 0xFF6F00 : 0xFFEB3B,
      });
      const p = new THREE.Mesh(geo, mat);
      p.position.set(
        (Math.random() - 0.5) * 0.5,
        Math.random() * 0.5,
        (Math.random() - 0.5) * 0.5
      );
      p.userData.vel = new THREE.Vector3(
        (Math.random() - 0.5) * 0.15,
        Math.random() * 0.25,
        (Math.random() - 0.5) * 0.15
      );
      p.userData.life = Math.random();
      group.add(p);
      particles.push(p);
    }
    this.scene.add(group);
    return { group, particles };
  }

  updateMachineStates(machineData) {
    if (!machineData) return;
    this.machineStates = machineData;

    Object.entries(machineData).forEach(([id, data]) => {
      const obj = this.machineObjects[id];
      if (!obj) return;
      const status = data.status || 'normal';
      const health = data.health_score || 100;

      // Update body color
      const color = this.machineColors[status] || this.machineColors.normal;
      obj.bodyMat.color.setHex(color);

      // Update status light
      const lightColors = {
        normal: 0x4CAF50, warning: 0xFF9800, critical: 0xF44336,
        failure: 0x9C27B0, healing: 0x00E676, offline: 0x607D8B,
      };
      const lc = lightColors[status] || lightColors.normal;
      obj.statusLightMat.color.setHex(lc);
      obj.statusLightMat.emissive.setHex(lc);
      obj.statusLightMat.emissiveIntensity = status === 'critical' || status === 'failure' ? 1.0 : 0.5;

      // Warning light brightness
      obj.warnLightMat.emissiveIntensity = status === 'warning' || status === 'critical' ? 0.8 : 0;

      // Heatmap color by health
      const hmColor = health >= 75 ? 0x4CAF50 : health >= 45 ? 0xFF9800 : 0xF44336;
      obj.hmMat.color.setHex(hmColor);
      obj.hmMat.opacity = this.heatmapVisible ? 0.20 : 0.0;
      if (this.heatmapPlanes[id]) {
        this.heatmapPlanes[id].mat.color.setHex(hmColor);
        this.heatmapPlanes[id].mat.opacity = this.heatmapVisible ? 0.15 : 0.0;
      }

      // Sparks for critical/failure
      if ((status === 'critical' || status === 'failure') && !obj.sparks) {
        obj.sparks = this._createSparkSystem(this.machinePositions[id]);
        this.sparkSystems.push({ ...obj.sparks, machineId: id });
      } else if (status === 'normal' || status === 'healing') {
        if (obj.sparks) {
          this.scene.remove(obj.sparks.group);
          obj.sparks = null;
          this.sparkSystems = this.sparkSystems.filter(s => s.machineId !== id);
        }
      }
    });

    // Update pipeline colors
    this.pipes.forEach(pipe => {
      const fromStatus = machineData[pipe.fromMachine]?.status || 'normal';
      const toStatus = machineData[pipe.toMachine]?.status || 'normal';
      const worstStatus = ['failure', 'critical', 'warning', 'healing', 'normal', 'offline']
        .find(s => s === fromStatus || s === toStatus) || 'normal';
      const pc = this.pipeColors[worstStatus] || this.pipeColors.normal;
      pipe.mat.color.setHex(pc);
      pipe.mat.emissive.setHex(pc);
      pipe.mat.emissiveIntensity = worstStatus === 'failure' ? 0.3 : worstStatus === 'critical' ? 0.2 : 0.05;
    });
  }

  _onCanvasClick(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this.mouse, this.camera);

    const objects = Object.values(this.machineObjects).map(m => m.body);
    const intersects = this.raycaster.intersectObjects(objects, true);
    if (intersects.length > 0) {
      let obj = intersects[0].object;
      let machineId = obj.userData.machineId;
      if (!machineId && obj.parent) machineId = obj.parent.userData.machineId;
      if (machineId) {
        this.selectedMachine = machineId;
        this._showMachineInfo(machineId);
        // Highlight selected machine
        Object.entries(this.machineObjects).forEach(([id, mObj]) => {
          mObj.body.scale.set(id === machineId ? 1.05 : 1.0, 1.0, id === machineId ? 1.05 : 1.0);
        });
      }
    }
  }

  _showMachineInfo(machineId) {
    const overlay = document.getElementById('machine-info-overlay');
    if (!overlay) return;
    const state = this.machineStates[machineId];
    if (!state) return;

    const sensors = state.sensors || {};
    const health = state.health_score || 100;
    const status = state.status || 'normal';
    const needsAction = status === 'failure' || status === 'critical';

    const getClass = (val, warn, crit) => val >= crit ? 'critical' : val >= warn ? 'warning' : '';

    overlay.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <h4 style="color:var(--primary);font-size:13px;font-weight:700">${machineId}: ${state.name || machineId}</h4>
        ${needsAction ? '<span class="need-action-tag">Need Action</span>' : ''}
        <button onclick="this.closest('.machine-info-overlay').style.display='none'" style="background:none;border:none;cursor:pointer;font-size:16px;color:#999">✕</button>
      </div>
      <div class="sensor-row"><span class="sensor-label">Status</span><span class="sensor-value ${getClass(status==='critical'?90:status==='warning'?75:0, 75, 90)}">${status.toUpperCase()}</span></div>
      <div class="sensor-row"><span class="sensor-label">Temperature</span><span class="sensor-value ${getClass(sensors.temperature||0, 75, 90)}">${(sensors.temperature||0).toFixed(1)}°C</span></div>
      <div class="sensor-row"><span class="sensor-label">Vibration</span><span class="sensor-value ${getClass(sensors.vibration||0, 7, 10)}">${(sensors.vibration||0).toFixed(2)} mm/s</span></div>
      <div class="sensor-row"><span class="sensor-label">Motor Current</span><span class="sensor-value ${getClass(sensors.motor_current||0, 80, 95)}">${(sensors.motor_current||0).toFixed(1)} A</span></div>
      <div class="sensor-row"><span class="sensor-label">Speed</span><span class="sensor-value">${(sensors.speed||0).toFixed(0)} rpm</span></div>
      <div class="sensor-row"><span class="sensor-label">Load</span><span class="sensor-value ${getClass(sensors.load||0, 80, 95)}">${(sensors.load||0).toFixed(1)}%</span></div>
      <div class="sensor-row"><span class="sensor-label">Prod. Rate</span><span class="sensor-value">${(sensors.production_rate||0).toFixed(1)}%</span></div>
      <div class="health-bar-container">
        <div style="display:flex;justify-content:space-between;margin-bottom:3px">
          <span style="font-size:11px;color:var(--text-muted)">Health Score</span>
          <span style="font-size:12px;font-weight:700;color:${health>=70?'var(--success)':health>=40?'var(--warning)':'var(--danger)'}">${health.toFixed(1)}%</span>
        </div>
        <div class="health-bar-track">
          <div class="health-bar-fill" style="width:${health}%;background:${health>=70?'var(--success)':health>=40?'var(--warning)':'var(--danger)'}"></div>
        </div>
      </div>
      ${state.is_under_cyber_attack ? '<div style="margin-top:8px;background:rgba(231,76,60,0.1);border:1px solid rgba(231,76,60,0.3);border-radius:6px;padding:6px 8px;font-size:11px;color:var(--danger);font-weight:600">🛡️ UNDER CYBER ATTACK</div>' : ''}
    `;
    overlay.classList.add('visible');
    overlay.style.display = 'block';
  }

  _animate() {
    this.animFrameId = requestAnimationFrame(() => this._animate());
    const delta = this.clock.getDelta();
    const elapsed = this.clock.getElapsedTime();

    // Animate conveyor belts (move texture offset)
    this._conveyorOffset += delta * 0.8;
    this.conveyorBelts.forEach(cb => {
      cb.beltTex.offset.x = -this._conveyorOffset;
    });

    // Animate conveyor items
    this.conveyorItems.forEach(item => {
      item.progress += item.speed;
      if (item.progress > 1) item.progress = 0;
      item.mesh.position.x = item.fromX + (item.toX - item.fromX) * item.progress;
      item.mesh.rotation.y += delta * 0.5;
    });

    // Animate robotic arms
    this.robotArms.forEach(arm => {
      arm.lowerGroup.rotation.z = Math.sin(elapsed * 0.8 + arm.phase) * 0.3;
      arm.upperGroup.rotation.z = Math.sin(elapsed * 1.2 + arm.phase + 1) * 0.4;
      arm.group.rotation.y = Math.sin(elapsed * 0.5 + arm.phase) * 0.6;
    });

    // Animate forklifts
    this.forklifts.forEach(fl => {
      fl.progress += fl.speed * delta;
      if (fl.progress > 1) { fl.progress = 0; fl.group.rotation.y += Math.PI; }
      const x = fl.startX + (fl.endX - fl.startX) * fl.progress;
      fl.group.position.x = x;
      fl.group.position.z = fl.zPos + Math.sin(elapsed * 0.3) * 0.5;
    });

    // Machine effects
    Object.entries(this.machineObjects).forEach(([id, obj]) => {
      const state = this.machineStates[id] || {};
      const status = state.status || 'normal';
      const vibration = state.sensors?.vibration || 0;

      // Vibration shake effect
      if (status === 'critical' || status === 'failure' || vibration > 7) {
        const shakeMag = status === 'failure' ? 0.08 : 0.04;
        obj.group.position.x = obj.originalPos.x + Math.sin(elapsed * 40 + obj.shakePhase) * shakeMag;
        obj.group.position.z = obj.originalPos.z + Math.cos(elapsed * 37 + obj.shakePhase) * shakeMag;
      } else {
        obj.group.position.x = obj.originalPos.x;
        obj.group.position.z = obj.originalPos.z;
      }

      // Warning light pulse
      if (status === 'warning') {
        obj.warnLightMat.emissiveIntensity = 0.4 + Math.sin(elapsed * 4) * 0.4;
      } else if (status === 'critical') {
        obj.warnLightMat.emissiveIntensity = 0.5 + Math.sin(elapsed * 8) * 0.5;
      }

      // Status light pulse on healing
      if (status === 'healing') {
        obj.statusLightMat.emissiveIntensity = 0.3 + Math.sin(elapsed * 3) * 0.3;
      }
    });

    // Animate spark particles
    this.sparkSystems.forEach(sys => {
      sys.particles.forEach(p => {
        p.userData.life -= delta * 0.8;
        if (p.userData.life <= 0) {
          p.userData.life = 1.0;
          p.position.set(
            (Math.random() - 0.5) * 0.5,
            Math.random() * 0.3,
            (Math.random() - 0.5) * 0.5
          );
          p.userData.vel.set(
            (Math.random() - 0.5) * 0.15,
            Math.random() * 0.2,
            (Math.random() - 0.5) * 0.15
          );
        }
        p.position.addScaledVector(p.userData.vel, delta * 2);
        p.userData.vel.y -= delta * 0.5;
        p.material.opacity = p.userData.life;
      });
    });

    this.renderer.render(this.scene, this.camera);
  }

  _onResize() {
    if (!this.container) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  toggleHeatmap(visible) {
    this.heatmapVisible = visible;
    Object.values(this.heatmapPlanes).forEach(hp => {
      hp.mat.opacity = visible ? 0.15 : 0.0;
    });
    Object.values(this.machineObjects).forEach(obj => {
      obj.hmMat.opacity = visible ? 0.20 : 0.0;
    });
  }

  togglePipelines(visible) {
    this.pipelinesVisible = visible;
    this.pipes.forEach(p => {
      p.mesh.visible = visible;
    });
  }

  resetCamera() {
    if (this._orbitState) {
      this._orbitState.spherical.theta = 0;
      this._orbitState.spherical.phi = Math.PI / 4;
      this._orbitState.spherical.radius = 50;
      this._orbitState.panTarget.set(0, 2, 0);
      this._orbitState.updateCamera();
    }
  }

  focusMachine(machineId) {
    const pos = this.machinePositions[machineId];
    if (pos && this._orbitState) {
      this._orbitState.panTarget.set(pos.x, 2, 0);
      this._orbitState.spherical.radius = 20;
      this._orbitState.updateCamera();
    }
  }

  destroy() {
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    if (this.renderer && this.container) {
      this.container.removeChild(this.renderer.domElement);
      this.renderer.dispose();
    }
  }
}

/**
 * Poseidon 3D Animation System
 * Advanced 3D rendering of Poseidon with trident, lip-sync, and blue theme
 * Version: 3.x
 * ~4000 lines of advanced 3D animation code
 */

class Poseidon3D {
    constructor(containerElement) {
        this.container = containerElement;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.animationId = null;
        
        // Poseidon character components
        this.poseidon = null;
        this.body = null;
        this.head = null;
        this.mouth = null;
        this.eyes = null;
        this.beard = null;
        this.hair = null;
        this.arms = null;
        this.legs = null;
        this.trident = null;
        
        // Animation state
        this.isSpeaking = false;
        this.speechTime = 0;
        this.mouthOpenness = 0;
        this.currentPhoneme = null;
        this.animationSpeed = 1.0;
        
        // Lip-sync data
        this.phonemeMap = {
            'silence': 0.0,
            'A': 0.8, 'E': 0.6, 'I': 0.4, 'O': 0.9, 'U': 0.7,
            'M': 0.3, 'P': 0.5, 'B': 0.5, 'F': 0.4, 'V': 0.4,
            'TH': 0.3, 'S': 0.2, 'Z': 0.2, 'SH': 0.3, 'CH': 0.4,
            'L': 0.3, 'R': 0.4, 'T': 0.2, 'D': 0.3, 'N': 0.3,
            'K': 0.2, 'G': 0.3, 'Y': 0.5, 'W': 0.6, 'H': 0.5
        };
        
        // Blue color palette
        this.colors = {
            skin: 0x4a90e2,      // Blue-tinted skin
            skinDark: 0x357abd,
            hair: 0x1e3a8a,      // Dark blue hair
            beard: 0x1e40af,
            eye: 0x00d4ff,       // Bright blue eyes
            eyePupil: 0x001f3f,
            robe: 0x0ea5e9,      // Light blue robe
            robeDark: 0x0284c7,
            trident: 0x1e90ff,   // Bright blue trident
            tridentGold: 0xffd700,
            water: 0x00bfff,
            waterDark: 0x0066cc
        };
        
        // Animation parameters
        this.breatheAmplitude = 0.02;
        this.breatheSpeed = 0.5;
        this.breathePhase = 0;
        this.headBob = 0;
        this.tridentSway = 0;
        
        // Particle systems
        this.waterParticles = null;
        this.mistParticles = null;
        
        // Lighting
        this.ambientLight = null;
        this.mainLight = null;
        this.fillLight = null;
        this.rimLight = null;
        this.waterLight = null;
        
        // Post-processing (if available)
        this.composer = null;
        
        // Performance
        this.frameCount = 0;
        this.lastFrameTime = performance.now();
        this.fps = 60;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('[Poseidon3D] Container element not found');
            return;
        }
        
        const width = this.container.clientWidth || 800;
        const height = this.container.clientHeight || 600;
        
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a1a2e); // Deep blue background
        this.scene.fog = new THREE.Fog(0x0a1a2e, 50, 200);
        
        // Create camera
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(0, 2, 8);
        this.camera.lookAt(0, 1.5, 0);
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: false,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        
        this.container.appendChild(this.renderer.domElement);
        
        // Setup lighting
        this.setupLighting();
        
        // Create environment
        this.createEnvironment();
        
        // Create Poseidon character
        this.createPoseidon();
        
        // Create trident
        this.createTrident();
        
        // Create particle effects
        this.createParticleEffects();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Start performance monitoring
        this.startPerformanceMonitoring();
        
        // Start animation loop
        this.animate();
        
        // Enhance with advanced features
        setTimeout(() => this.enhanceInitialization(), 100);
        
        console.log('[Poseidon3D] Initialized successfully');
    }
    
    setupLighting() {
        // Ambient light (soft blue)
        this.ambientLight = new THREE.AmbientLight(0x4a90e2, 0.4);
        this.scene.add(this.ambientLight);
        
        // Main directional light (from top-left, blue-white)
        this.mainLight = new THREE.DirectionalLight(0x87ceeb, 1.2);
        this.mainLight.position.set(5, 10, 5);
        this.mainLight.castShadow = true;
        this.mainLight.shadow.mapSize.width = 2048;
        this.mainLight.shadow.mapSize.height = 2048;
        this.mainLight.shadow.camera.near = 0.5;
        this.mainLight.shadow.camera.far = 50;
        this.mainLight.shadow.camera.left = -10;
        this.mainLight.shadow.camera.right = 10;
        this.mainLight.shadow.camera.top = 10;
        this.mainLight.shadow.camera.bottom = -10;
        this.mainLight.shadow.bias = -0.0001;
        this.scene.add(this.mainLight);
        
        // Fill light (from right, softer blue)
        this.fillLight = new THREE.DirectionalLight(0x5dade2, 0.6);
        this.fillLight.position.set(-5, 3, 5);
        this.scene.add(this.fillLight);
        
        // Rim light (from behind, bright blue)
        this.rimLight = new THREE.DirectionalLight(0x00bfff, 0.8);
        this.rimLight.position.set(0, 2, -10);
        this.scene.add(this.rimLight);
        
        // Point light for water glow
        this.waterLight = new THREE.PointLight(0x00d4ff, 1.5, 20);
        this.waterLight.position.set(0, 0, 0);
        this.scene.add(this.waterLight);
    }
    
    createEnvironment() {
        // Ocean floor/base
        const floorGeometry = new THREE.PlaneGeometry(50, 50, 32, 32);
        const floorMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a5490,
            roughness: 0.8,
            metalness: 0.1
        });
        
        // Add wave displacement to floor
        const floorPositions = floorGeometry.attributes.position;
        for (let i = 0; i < floorPositions.count; i++) {
            const x = floorPositions.getX(i);
            const z = floorPositions.getY(i);
            const wave = Math.sin(x * 0.5) * Math.cos(z * 0.5) * 0.3;
            floorPositions.setZ(i, wave);
        }
        floorGeometry.computeVertexNormals();
        
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = -0.5;
        floor.receiveShadow = true;
        this.scene.add(floor);
        
        // Background water effect (volumetric)
        const waterGroup = new THREE.Group();
        
        // Multiple layers of water particles for depth
        for (let layer = 0; layer < 5; layer++) {
            const waterGeometry = new THREE.PlaneGeometry(30, 30, 20, 20);
            const waterMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.water,
                transparent: true,
                opacity: 0.1 - layer * 0.015,
                side: THREE.DoubleSide,
                roughness: 0.1,
                metalness: 0.3,
                emissive: this.colors.water,
                emissiveIntensity: 0.2
            });
            
            const waterPlane = new THREE.Mesh(waterGeometry, waterMaterial);
            waterPlane.position.z = -5 - layer * 2;
            waterPlane.rotation.x = Math.PI / 4;
            waterGroup.add(waterPlane);
        }
        
        this.scene.add(waterGroup);
        this.waterGroup = waterGroup;
    }
    
    createPoseidon() {
        const poseidonGroup = new THREE.Group();
        
        // Body (torso)
        const bodyGeometry = new THREE.CylinderGeometry(0.6, 0.8, 1.8, 16);
        const bodyMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skin,
            roughness: 0.7,
            metalness: 0.1
        });
        this.body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        this.body.position.y = 0.9;
        this.body.castShadow = true;
        this.body.receiveShadow = true;
        poseidonGroup.add(this.body);
        
        // Add muscle definition to body
        this.addBodyDetails();
        
        // Head
        this.createHead();
        this.head.position.y = 2.2;
        poseidonGroup.add(this.head);
        
        // Arms
        this.createArms();
        poseidonGroup.add(this.arms);
        
        // Legs
        this.createLegs();
        poseidonGroup.add(this.legs);
        
        // Robe/cloak
        this.createRobe();
        poseidonGroup.add(this.robeGroup);
        
        poseidonGroup.position.y = 0;
        this.scene.add(poseidonGroup);
        this.poseidon = poseidonGroup;
    }
    
    addBodyDetails() {
        // Chest muscles
        const chestGeometry = new THREE.SphereGeometry(0.3, 12, 8);
        const chestMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skinDark,
            roughness: 0.6
        });
        
        const leftChest = new THREE.Mesh(chestGeometry, chestMaterial);
        leftChest.position.set(-0.2, 2.0, 0.5);
        leftChest.scale.set(1, 0.8, 0.5);
        this.body.add(leftChest);
        
        const rightChest = new THREE.Mesh(chestGeometry, chestMaterial);
        rightChest.position.set(0.2, 2.0, 0.5);
        rightChest.scale.set(1, 0.8, 0.5);
        this.body.add(rightChest);
        
        // Abs definition
        for (let i = 0; i < 4; i++) {
            const absGeometry = new THREE.BoxGeometry(0.4, 0.1, 0.05);
            const absMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.skinDark,
                roughness: 0.5
            });
            const abs = new THREE.Mesh(absGeometry, absMaterial);
            abs.position.set(0, 1.2 - i * 0.15, 0.52);
            this.body.add(abs);
        }
    }
    
    createHead() {
        const headGroup = new THREE.Group();
        
        // Main head sphere
        const headGeometry = new THREE.SphereGeometry(0.4, 32, 32);
        const headMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skin,
            roughness: 0.7,
            metalness: 0.1
        });
        const headMesh = new THREE.Mesh(headGeometry, headMaterial);
        headMesh.castShadow = true;
        headMesh.receiveShadow = true;
        headGroup.add(headMesh);
        this.headMesh = headMesh;
        
        // Facial features
        this.createEyes(headGroup);
        this.createNose(headGroup);
        this.createMouth(headGroup);
        this.createBeard(headGroup);
        this.createHair(headGroup);
        this.createEars(headGroup);
        
        this.head = headGroup;
    }
    
    createEyes(headGroup) {
        const eyesGroup = new THREE.Group();
        
        // Eye sockets
        const socketGeometry = new THREE.SphereGeometry(0.08, 16, 16);
        const socketMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a2e,
            roughness: 0.8
        });
        
        const leftSocket = new THREE.Mesh(socketGeometry, socketMaterial);
        leftSocket.position.set(-0.15, 0.1, 0.35);
        leftSocket.scale.set(1, 0.6, 0.3);
        eyesGroup.add(leftSocket);
        
        const rightSocket = new THREE.Mesh(socketGeometry, socketMaterial);
        rightSocket.position.set(0.15, 0.1, 0.35);
        rightSocket.scale.set(1, 0.6, 0.3);
        eyesGroup.add(rightSocket);
        
        // Eyeballs
        const eyeGeometry = new THREE.SphereGeometry(0.06, 16, 16);
        const eyeMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.eye,
            emissive: this.colors.eye,
            emissiveIntensity: 0.5,
            roughness: 0.2,
            metalness: 0.8
        });
        
        this.leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        this.leftEye.position.set(-0.15, 0.1, 0.38);
        eyesGroup.add(this.leftEye);
        
        this.rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        this.rightEye.position.set(0.15, 0.1, 0.38);
        eyesGroup.add(this.rightEye);
        
        // Pupils
        const pupilGeometry = new THREE.SphereGeometry(0.025, 12, 12);
        const pupilMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.eyePupil
        });
        
        this.leftPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);
        this.leftPupil.position.set(0, 0, 0.03);
        this.leftEye.add(this.leftPupil);
        
        this.rightPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);
        this.rightPupil.position.set(0, 0, 0.03);
        this.rightEye.add(this.rightPupil);
        
        // Eyebrows
        const browGeometry = new THREE.BoxGeometry(0.12, 0.02, 0.01);
        const browMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.hair
        });
        
        const leftBrow = new THREE.Mesh(browGeometry, browMaterial);
        leftBrow.position.set(-0.15, 0.18, 0.36);
        leftBrow.rotation.z = -0.2;
        eyesGroup.add(leftBrow);
        
        const rightBrow = new THREE.Mesh(browGeometry, browMaterial);
        rightBrow.position.set(0.15, 0.18, 0.36);
        rightBrow.rotation.z = 0.2;
        eyesGroup.add(rightBrow);
        
        headGroup.add(eyesGroup);
        this.eyes = eyesGroup;
    }
    
    createNose(headGroup) {
        const noseGeometry = new THREE.ConeGeometry(0.05, 0.15, 8);
        const noseMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skinDark,
            roughness: 0.6
        });
        const nose = new THREE.Mesh(noseGeometry, noseMaterial);
        nose.position.set(0, 0, 0.38);
        nose.rotation.x = Math.PI;
        headGroup.add(nose);
    }
    
    createMouth(headGroup) {
        const mouthGroup = new THREE.Group();
        
        // Mouth base (closed)
        const mouthGeometry = new THREE.TorusGeometry(0.08, 0.02, 8, 16);
        const mouthMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a1a1a,
            roughness: 0.8
        });
        
        this.mouthBase = new THREE.Mesh(mouthGeometry, mouthMaterial);
        this.mouthBase.position.set(0, -0.12, 0.38);
        this.mouthBase.rotation.x = Math.PI / 2;
        mouthGroup.add(this.mouthBase);
        
        // Mouth opening (animated)
        this.mouthOpening = new THREE.Group();
        
        // Upper lip
        this.upperLip = new THREE.Mesh(
            new THREE.RingGeometry(0.05, 0.08, 8, 1),
            new THREE.MeshStandardMaterial({ color: this.colors.skinDark })
        );
        this.upperLip.rotation.x = Math.PI / 2;
        this.upperLip.position.y = 0.01;
        this.mouthOpening.add(this.upperLip);
        
        // Lower lip
        this.lowerLip = new THREE.Mesh(
            new THREE.RingGeometry(0.05, 0.08, 8, 1),
            new THREE.MeshStandardMaterial({ color: this.colors.skinDark })
        );
        this.lowerLip.rotation.x = -Math.PI / 2;
        this.lowerLip.position.y = -0.01;
        this.mouthOpening.add(this.lowerLip);
        
        // Mouth interior (tongue/teeth)
        this.mouthInterior = new THREE.Mesh(
            new THREE.CylinderGeometry(0.07, 0.07, 0.05, 16),
            new THREE.MeshStandardMaterial({ 
                color: 0x4a4a4a,
                roughness: 0.9
            })
        );
        this.mouthInterior.rotation.x = Math.PI / 2;
        this.mouthInterior.position.z = 0.02;
        this.mouthOpening.add(this.mouthInterior);
        
        this.mouthOpening.position.set(0, -0.12, 0.38);
        this.mouthOpening.scale.y = 0; // Start closed
        mouthGroup.add(this.mouthOpening);
        
        headGroup.add(mouthGroup);
        this.mouth = mouthGroup;
    }
    
    createBeard(headGroup) {
        const beardGroup = new THREE.Group();
        const beardMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.beard,
            roughness: 0.8,
            metalness: 0.1
        });
        
        // Main beard volume
        const beardGeometry = new THREE.ConeGeometry(0.25, 0.4, 12);
        const mainBeard = new THREE.Mesh(beardGeometry, beardMaterial);
        mainBeard.position.set(0, -0.35, 0.3);
        mainBeard.rotation.x = Math.PI;
        mainBeard.scale.set(1.2, 1, 0.8);
        beardGroup.add(mainBeard);
        
        // Individual beard strands for detail
        for (let i = 0; i < 20; i++) {
            const strandGeometry = new THREE.CylinderGeometry(0.008, 0.008, 0.15 + Math.random() * 0.1, 6);
            const strand = new THREE.Mesh(strandGeometry, beardMaterial);
            const angle = (i / 20) * Math.PI * 2;
            const radius = 0.2 + Math.random() * 0.1;
            strand.position.set(
                Math.cos(angle) * radius,
                -0.25 - Math.random() * 0.2,
                0.3 + Math.sin(angle) * radius * 0.3
            );
            strand.rotation.x = -0.3 + Math.random() * 0.6;
            strand.rotation.z = angle + (Math.random() - 0.5) * 0.3;
            beardGroup.add(strand);
        }
        
        headGroup.add(beardGroup);
        this.beard = beardGroup;
    }
    
    createHair(headGroup) {
        const hairGroup = new THREE.Group();
        const hairMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.hair,
            roughness: 0.7,
            metalness: 0.2
        });
        
        // Main hair volume
        const hairGeometry = new THREE.SphereGeometry(0.45, 16, 12);
        const mainHair = new THREE.Mesh(hairGeometry, hairMaterial);
        mainHair.position.set(0, 0.15, -0.1);
        mainHair.scale.set(1, 0.9, 0.7);
        hairGroup.add(mainHair);
        
        // Hair strands/waves
        for (let i = 0; i < 30; i++) {
            const points = [];
            const numPoints = 8;
            for (let j = 0; j < numPoints; j++) {
                const t = j / (numPoints - 1);
                const angle = (i / 30) * Math.PI * 2;
                const radius = 0.4 + Math.sin(t * Math.PI) * 0.1;
                points.push(new THREE.Vector3(
                    Math.cos(angle) * radius * (1 - t * 0.5),
                    0.1 + Math.sin(t * Math.PI) * 0.3,
                    -0.1 - t * 0.4 + Math.sin(angle * 2) * 0.1
                ));
            }
            
            const curve = new THREE.CatmullRomCurve3(points);
            const strandGeometry = new THREE.TubeGeometry(curve, numPoints * 2, 0.015, 8, false);
            const strand = new THREE.Mesh(strandGeometry, hairMaterial);
            hairGroup.add(strand);
        }
        
        headGroup.add(hairGroup);
        this.hair = hairGroup;
    }
    
    createEars(headGroup) {
        const earGeometry = new THREE.ConeGeometry(0.08, 0.12, 8);
        const earMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skin,
            roughness: 0.7
        });
        
        const leftEar = new THREE.Mesh(earGeometry, earMaterial);
        leftEar.position.set(-0.38, 0, 0.15);
        leftEar.rotation.y = Math.PI / 2;
        leftEar.rotation.z = -Math.PI / 6;
        headGroup.add(leftEar);
        
        const rightEar = new THREE.Mesh(earGeometry, earMaterial);
        rightEar.position.set(0.38, 0, 0.15);
        rightEar.rotation.y = -Math.PI / 2;
        rightEar.rotation.z = Math.PI / 6;
        headGroup.add(rightEar);
    }
    
    createArms() {
        const armsGroup = new THREE.Group();
        
        // Left arm (holding trident)
        const leftArmGroup = new THREE.Group();
        
        // Left shoulder
        const leftShoulderGeometry = new THREE.SphereGeometry(0.2, 16, 16);
        const shoulderMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skin,
            roughness: 0.7
        });
        const leftShoulder = new THREE.Mesh(leftShoulderGeometry, shoulderMaterial);
        leftShoulder.position.set(-0.7, 2.0, 0);
        leftShoulder.castShadow = true;
        leftArmGroup.add(leftShoulder);
        
        // Left upper arm
        const leftUpperArmGeometry = new THREE.CylinderGeometry(0.12, 0.15, 0.5, 12);
        const leftUpperArm = new THREE.Mesh(leftUpperArmGeometry, shoulderMaterial);
        leftUpperArm.position.set(-0.7, 1.6, 0);
        leftUpperArm.rotation.z = Math.PI / 6;
        leftUpperArm.castShadow = true;
        leftArmGroup.add(leftUpperArm);
        
        // Left elbow
        const leftElbow = new THREE.Mesh(leftShoulderGeometry, shoulderMaterial);
        leftElbow.scale.set(0.7, 0.7, 0.7);
        leftElbow.position.set(-0.85, 1.35, 0);
        leftElbow.castShadow = true;
        leftArmGroup.add(leftElbow);
        
        // Left forearm
        const leftForearmGeometry = new THREE.CylinderGeometry(0.1, 0.12, 0.5, 12);
        const leftForearm = new THREE.Mesh(leftForearmGeometry, shoulderMaterial);
        leftForearm.position.set(-0.95, 1.05, 0);
        leftForearm.rotation.z = Math.PI / 4;
        leftForearm.castShadow = true;
        leftArmGroup.add(leftForearm);
        
        // Left hand
        this.createHand(leftArmGroup, -1.05, 0.75, 0, true);
        
        leftArmGroup.position.set(0, 0, 0);
        armsGroup.add(leftArmGroup);
        this.leftArm = leftArmGroup;
        
        // Right arm (relaxed)
        const rightArmGroup = new THREE.Group();
        
        // Right shoulder
        const rightShoulder = new THREE.Mesh(leftShoulderGeometry, shoulderMaterial);
        rightShoulder.position.set(0.7, 2.0, 0);
        rightShoulder.castShadow = true;
        rightArmGroup.add(rightShoulder);
        
        // Right upper arm
        const rightUpperArm = new THREE.Mesh(leftUpperArmGeometry, shoulderMaterial);
        rightUpperArm.position.set(0.7, 1.6, 0);
        rightUpperArm.rotation.z = -Math.PI / 6;
        rightUpperArm.castShadow = true;
        rightArmGroup.add(rightUpperArm);
        
        // Right elbow
        const rightElbow = new THREE.Mesh(leftShoulderGeometry, shoulderMaterial);
        rightElbow.scale.set(0.7, 0.7, 0.7);
        rightElbow.position.set(0.85, 1.35, 0);
        rightElbow.castShadow = true;
        rightArmGroup.add(rightElbow);
        
        // Right forearm
        const rightForearm = new THREE.Mesh(leftForearmGeometry, shoulderMaterial);
        rightForearm.position.set(0.9, 1.05, 0);
        rightForearm.rotation.z = -Math.PI / 3;
        rightForearm.castShadow = true;
        rightArmGroup.add(rightForearm);
        
        // Right hand
        this.createHand(rightArmGroup, 0.95, 0.75, 0, false);
        
        rightArmGroup.position.set(0, 0, 0);
        armsGroup.add(rightArmGroup);
        this.rightArm = rightArmGroup;
        
        armsGroup.position.set(0, 0, 0);
        this.arms = armsGroup;
    }
    
    createHand(parentGroup, x, y, z, isLeft) {
        const handGroup = new THREE.Group();
        const handMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skin,
            roughness: 0.7
        });
        
        // Palm
        const palmGeometry = new THREE.BoxGeometry(0.12, 0.08, 0.04);
        const palm = new THREE.Mesh(palmGeometry, handMaterial);
        palm.position.set(0, 0, 0);
        palm.castShadow = true;
        handGroup.add(palm);
        
        // Thumb
        const thumbGeometry = new THREE.CylinderGeometry(0.03, 0.035, 0.08, 8);
        const thumb = new THREE.Mesh(thumbGeometry, handMaterial);
        thumb.position.set(isLeft ? 0.06 : -0.06, -0.02, 0.02);
        thumb.rotation.z = isLeft ? -Math.PI / 4 : Math.PI / 4;
        thumb.rotation.x = Math.PI / 2;
        thumb.castShadow = true;
        handGroup.add(thumb);
        
        // Fingers
        for (let i = 0; i < 4; i++) {
            const fingerGeometry = new THREE.CylinderGeometry(0.025, 0.03, 0.1, 8);
            const finger = new THREE.Mesh(fingerGeometry, handMaterial);
            finger.position.set(
                (i - 1.5) * 0.03,
                0.05,
                0
            );
            finger.rotation.x = -Math.PI / 6;
            finger.castShadow = true;
            handGroup.add(finger);
        }
        
        handGroup.position.set(x, y, z);
        parentGroup.add(handGroup);
        
        if (isLeft) {
            this.leftHand = handGroup;
        } else {
            this.rightHand = handGroup;
        }
    }
    
    createLegs() {
        const legsGroup = new THREE.Group();
        const legMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skin,
            roughness: 0.7
        });
        
        // Left leg
        const leftLegGroup = new THREE.Group();
        
        // Left thigh
        const thighGeometry = new THREE.CylinderGeometry(0.15, 0.2, 0.7, 12);
        const leftThigh = new THREE.Mesh(thighGeometry, legMaterial);
        leftThigh.position.set(-0.25, 0.35, 0);
        leftThigh.castShadow = true;
        leftLegGroup.add(leftThigh);
        
        // Left knee
        const kneeGeometry = new THREE.SphereGeometry(0.12, 12, 12);
        const leftKnee = new THREE.Mesh(kneeGeometry, legMaterial);
        leftKnee.position.set(-0.25, -0.05, 0);
        leftKnee.castShadow = true;
        leftLegGroup.add(leftKnee);
        
        // Left shin
        const shinGeometry = new THREE.CylinderGeometry(0.12, 0.15, 0.7, 12);
        const leftShin = new THREE.Mesh(shinGeometry, legMaterial);
        leftShin.position.set(-0.25, -0.45, 0);
        leftShin.castShadow = true;
        leftLegGroup.add(leftShin);
        
        // Left foot
        const footGeometry = new THREE.BoxGeometry(0.18, 0.08, 0.25);
        const leftFoot = new THREE.Mesh(footGeometry, legMaterial);
        leftFoot.position.set(-0.25, -0.85, 0.1);
        leftFoot.castShadow = true;
        leftLegGroup.add(leftFoot);
        
        legsGroup.add(leftLegGroup);
        
        // Right leg
        const rightLegGroup = new THREE.Group();
        
        // Right thigh
        const rightThigh = new THREE.Mesh(thighGeometry, legMaterial);
        rightThigh.position.set(0.25, 0.35, 0);
        rightThigh.castShadow = true;
        rightLegGroup.add(rightThigh);
        
        // Right knee
        const rightKnee = new THREE.Mesh(kneeGeometry, legMaterial);
        rightKnee.position.set(0.25, -0.05, 0);
        rightKnee.castShadow = true;
        rightLegGroup.add(rightKnee);
        
        // Right shin
        const rightShin = new THREE.Mesh(shinGeometry, legMaterial);
        rightShin.position.set(0.25, -0.45, 0);
        rightShin.castShadow = true;
        rightLegGroup.add(rightShin);
        
        // Right foot
        const rightFoot = new THREE.Mesh(footGeometry, legMaterial);
        rightFoot.position.set(0.25, -0.85, 0.1);
        rightFoot.castShadow = true;
        rightLegGroup.add(rightFoot);
        
        legsGroup.add(rightLegGroup);
        
        legsGroup.position.set(0, 0, 0);
        this.legs = legsGroup;
    }
    
    createRobe() {
        const robeGroup = new THREE.Group();
        const robeMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.robe,
            roughness: 0.6,
            metalness: 0.2,
            emissive: this.colors.robe,
            emissiveIntensity: 0.1
        });
        
        // Main robe body
        const robeGeometry = new THREE.CylinderGeometry(0.7, 1.0, 1.5, 16);
        const robe = new THREE.Mesh(robeGeometry, robeMaterial);
        robe.position.y = 0.5;
        robe.scale.set(1, 1, 0.8);
        robe.castShadow = true;
        robe.receiveShadow = true;
        robeGroup.add(robe);
        
        // Robe drapery/folds
        for (let i = 0; i < 8; i++) {
            const foldGeometry = new THREE.BoxGeometry(0.1, 1.5, 0.15);
            const foldMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.robeDark,
                roughness: 0.7
            });
            const fold = new THREE.Mesh(foldGeometry, foldMaterial);
            const angle = (i / 8) * Math.PI * 2;
            fold.position.set(
                Math.cos(angle) * 0.6,
                0.5,
                Math.sin(angle) * 0.5
            );
            fold.rotation.y = angle;
            fold.rotation.z = Math.sin(angle) * 0.1;
            fold.castShadow = true;
            robeGroup.add(fold);
        }
        
        // Cape/cloak
        const capeGeometry = new THREE.PlaneGeometry(1.2, 1.8, 8, 12);
        const capeMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.robeDark,
            side: THREE.DoubleSide,
            roughness: 0.5,
            metalness: 0.3
        });
        
        // Add wave to cape
        const capePositions = capeGeometry.attributes.position;
        for (let i = 0; i < capePositions.count; i++) {
            const x = capePositions.getX(i);
            const y = capePositions.getY(i);
            const wave = Math.sin(x * 2) * Math.cos(y * 1.5) * 0.2;
            capePositions.setZ(i, wave);
        }
        capeGeometry.computeVertexNormals();
        
        const cape = new THREE.Mesh(capeGeometry, capeMaterial);
        cape.position.set(0, 1.2, -0.5);
        cape.rotation.x = -Math.PI / 6;
        cape.castShadow = true;
        robeGroup.add(cape);
        
        this.robeGroup = robeGroup;
    }
    
    createTrident() {
        const tridentGroup = new THREE.Group();
        
        // Main shaft
        const shaftGeometry = new THREE.CylinderGeometry(0.04, 0.05, 2.5, 16);
        const shaftMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.trident,
            roughness: 0.3,
            metalness: 0.9,
            emissive: this.colors.trident,
            emissiveIntensity: 0.3
        });
        const shaft = new THREE.Mesh(shaftGeometry, shaftMaterial);
        shaft.position.y = 1.25;
        shaft.castShadow = true;
        tridentGroup.add(shaft);
        
        // Gold accents on shaft
        const goldMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.tridentGold,
            roughness: 0.2,
            metalness: 1.0,
            emissive: this.colors.tridentGold,
            emissiveIntensity: 0.2
        });
        
        for (let i = 0; i < 5; i++) {
            const ringGeometry = new THREE.TorusGeometry(0.045, 0.01, 8, 16);
            const ring = new THREE.Mesh(ringGeometry, goldMaterial);
            ring.position.y = 0.5 + i * 0.4;
            ring.rotation.x = Math.PI / 2;
            tridentGroup.add(ring);
        }
        
        // Three prongs
        const prongGroup = new THREE.Group();
        
        // Center prong
        const centerProngGeometry = new THREE.ConeGeometry(0.08, 0.6, 8);
        const prongMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.trident,
            roughness: 0.2,
            metalness: 0.95,
            emissive: this.colors.trident,
            emissiveIntensity: 0.4
        });
        const centerProng = new THREE.Mesh(centerProngGeometry, prongMaterial);
        centerProng.position.y = 2.8;
        centerProng.rotation.z = Math.PI;
        centerProng.castShadow = true;
        prongGroup.add(centerProng);
        
        // Left prong
        const leftProng = new THREE.Mesh(centerProngGeometry, prongMaterial);
        leftProng.position.set(-0.2, 2.75, 0);
        leftProng.rotation.z = Math.PI;
        leftProng.rotation.y = -0.3;
        leftProng.castShadow = true;
        prongGroup.add(leftProng);
        
        // Right prong
        const rightProng = new THREE.Mesh(centerProngGeometry, prongMaterial);
        rightProng.position.set(0.2, 2.75, 0);
        rightProng.rotation.z = Math.PI;
        rightProng.rotation.y = 0.3;
        rightProng.castShadow = true;
        prongGroup.add(rightProng);
        
        // Prong tips (lightning/electric effect)
        const tipGeometry = new THREE.SphereGeometry(0.06, 12, 12);
        const tipMaterial = new THREE.MeshStandardMaterial({
            color: 0x00ffff,
            emissive: 0x00ffff,
            emissiveIntensity: 1.0,
            roughness: 0.1,
            metalness: 0.9
        });
        
        const centerTip = new THREE.Mesh(tipGeometry, tipMaterial);
        centerTip.position.y = 3.1;
        prongGroup.add(centerTip);
        
        const leftTip = new THREE.Mesh(tipGeometry, tipMaterial);
        leftTip.position.set(-0.2, 3.05, 0);
        prongGroup.add(leftTip);
        
        const rightTip = new THREE.Mesh(tipGeometry, tipMaterial);
        rightTip.position.set(0.2, 3.05, 0);
        prongGroup.add(rightTip);
        
        tridentGroup.add(prongGroup);
        this.tridentProngs = prongGroup;
        
        // Position trident in left hand
        tridentGroup.position.set(-1.2, 0.75, 0);
        tridentGroup.rotation.z = Math.PI / 6;
        tridentGroup.rotation.y = -Math.PI / 4;
        
        // Attach to hand (will be parented in animation)
        this.scene.add(tridentGroup);
        this.trident = tridentGroup;
    }
    
    createParticleEffects() {
        // Water particles around Poseidon
        const waterParticleGeometry = new THREE.BufferGeometry();
        const waterParticleCount = 200;
        const waterPositions = new Float32Array(waterParticleCount * 3);
        const waterSizes = new Float32Array(waterParticleCount);
        
        for (let i = 0; i < waterParticleCount; i++) {
            const i3 = i * 3;
            const radius = 2 + Math.random() * 3;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;
            
            waterPositions[i3] = Math.sin(phi) * Math.cos(theta) * radius;
            waterPositions[i3 + 1] = Math.cos(phi) * radius + 1;
            waterPositions[i3 + 2] = Math.sin(phi) * Math.sin(theta) * radius;
            
            waterSizes[i] = 0.05 + Math.random() * 0.1;
        }
        
        waterParticleGeometry.setAttribute('position', new THREE.BufferAttribute(waterPositions, 3));
        waterParticleGeometry.setAttribute('size', new THREE.BufferAttribute(waterSizes, 1));
        
        const waterParticleMaterial = new THREE.PointsMaterial({
            color: this.colors.water,
            size: 0.1,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });
        
        this.waterParticles = new THREE.Points(waterParticleGeometry, waterParticleMaterial);
        this.scene.add(this.waterParticles);
        
        // Mist/steam particles
        const mistParticleGeometry = new THREE.BufferGeometry();
        const mistParticleCount = 100;
        const mistPositions = new Float32Array(mistParticleCount * 3);
        const mistSizes = new Float32Array(mistParticleCount);
        const mistOpacities = new Float32Array(mistParticleCount);
        
        for (let i = 0; i < mistParticleCount; i++) {
            const i3 = i * 3;
            mistPositions[i3] = (Math.random() - 0.5) * 4;
            mistPositions[i3 + 1] = Math.random() * 2;
            mistPositions[i3 + 2] = (Math.random() - 0.5) * 4;
            
            mistSizes[i] = 0.2 + Math.random() * 0.3;
            mistOpacities[i] = 0.1 + Math.random() * 0.3;
        }
        
        mistParticleGeometry.setAttribute('position', new THREE.BufferAttribute(mistPositions, 3));
        mistParticleGeometry.setAttribute('size', new THREE.BufferAttribute(mistSizes, 1));
        mistParticleGeometry.setAttribute('opacity', new THREE.BufferAttribute(mistOpacities, 1));
        
        const mistParticleMaterial = new THREE.PointsMaterial({
            color: 0xa0d8ff,
            size: 0.3,
            transparent: true,
            opacity: 0.2,
            blending: THREE.AdditiveBlending,
            vertexColors: false,
            sizeAttenuation: true
        });
        
        this.mistParticles = new THREE.Points(mistParticleGeometry, mistParticleMaterial);
        this.scene.add(this.mistParticles);
    }
    
    // Lip-sync and animation methods
    updateLipSync(phoneme, intensity = 1.0) {
        if (!this.mouth || !this.mouthOpening) return;
        
        const targetOpenness = this.phonemeMap[phoneme] || 0.3;
        this.mouthOpenness = THREE.MathUtils.lerp(this.mouthOpenness, targetOpenness * intensity, 0.3);
        
        // Update mouth opening scale
        this.mouthOpening.scale.y = this.mouthOpenness;
        this.mouthOpening.scale.x = 1.0 + this.mouthOpenness * 0.3;
        
        // Adjust mouth base visibility
        if (this.mouthBase) {
            this.mouthBase.scale.y = 1.0 - this.mouthOpenness * 0.8;
        }
    }
    
    analyzeTextForPhonemes(text) {
        // Simple phoneme extraction from text
        const phonemes = [];
        const lowerText = text.toLowerCase();
        
        for (let i = 0; i < lowerText.length; i++) {
            const char = lowerText[i];
            const nextChar = lowerText[i + 1];
            const twoChar = char + (nextChar || '');
            
            if (twoChar === 'th') {
                phonemes.push('TH');
                i++;
            } else if (twoChar === 'sh') {
                phonemes.push('SH');
                i++;
            } else if (twoChar === 'ch') {
                phonemes.push('CH');
                i++;
            } else if ('aeiou'.includes(char)) {
                phonemes.push(char.toUpperCase());
            } else if ('bcdfghjklmnpqrstvwxyz'.includes(char)) {
                phonemes.push(char.toUpperCase());
            } else {
                phonemes.push('silence');
            }
        }
        
        return phonemes;
    }
    
    startSpeaking(text, duration) {
        this.isSpeaking = true;
        this.speechTime = 0;
        this.speechDuration = duration || text.length * 0.1; // Estimate duration
        this.speechPhonemes = this.analyzeTextForPhonemes(text);
        this.phonemeIndex = 0;
        this.phonemeTime = 0;
        this.phonemeDuration = this.speechDuration / this.speechPhonemes.length;
    }
    
    stopSpeaking() {
        this.isSpeaking = false;
        this.mouthOpenness = 0;
        if (this.mouthOpening) {
            this.mouthOpening.scale.y = 0;
        }
        if (this.mouthBase) {
            this.mouthBase.scale.y = 1.0;
        }
    }
    
    // Animation loop
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        const currentTime = performance.now();
        const deltaTime = (currentTime - this.lastFrameTime) / 1000;
        this.lastFrameTime = currentTime;
        
        // Update breathing animation
        this.breathePhase += deltaTime * this.breatheSpeed;
        const breatheOffset = Math.sin(this.breathePhase) * this.breatheAmplitude;
        
        if (this.body) {
            this.body.scale.y = 1.0 + breatheOffset;
        }
        
        // Update head bob (subtle)
        this.headBob += deltaTime * 0.3;
        if (this.head) {
            this.head.position.y = 2.2 + Math.sin(this.headBob) * 0.02;
            this.head.rotation.y = Math.sin(this.headBob * 0.5) * 0.05;
        }
        
        // Update trident sway
        if (this.trident) {
            this.tridentSway += deltaTime * 0.4;
            this.trident.rotation.z = Math.PI / 6 + Math.sin(this.tridentSway) * 0.05;
            this.trident.rotation.y = -Math.PI / 4 + Math.cos(this.tridentSway * 0.7) * 0.03;
            
            // Animate trident tips (electric effect)
            if (this.tridentProngs) {
                const electricPhase = currentTime * 0.01;
                this.tridentProngs.children.forEach((prong, index) => {
                    if (prong.type === 'Mesh' && prong.material.emissive) {
                        const intensity = 0.5 + Math.sin(electricPhase + index) * 0.5;
                        prong.material.emissiveIntensity = intensity;
                    }
                });
            }
        }
        
        // Update lip-sync if speaking
        if (this.isSpeaking) {
            this.speechTime += deltaTime;
            this.phonemeTime += deltaTime;
            
            if (this.phonemeTime >= this.phonemeDuration && this.phonemeIndex < this.speechPhonemes.length - 1) {
                this.phonemeIndex++;
                this.phonemeTime = 0;
            }
            
            const currentPhoneme = this.speechPhonemes[this.phonemeIndex] || 'silence';
            const progress = this.phonemeTime / this.phonemeDuration;
            const intensity = 1.0 - Math.abs(progress - 0.5) * 2; // Fade in/out
            
            this.updateLipSync(currentPhoneme, intensity);
        } else {
            // Gradually close mouth when not speaking
            this.updateLipSync('silence', 1.0);
        }
        
        // Update eye blinking
        if (this.leftEye && this.rightEye) {
            const blinkPhase = Math.sin(currentTime * 0.001) * 0.5 + 0.5;
            if (blinkPhase > 0.9) {
                const blinkAmount = (blinkPhase - 0.9) * 10;
                this.leftEye.scale.y = 1.0 - blinkAmount * 0.8;
                this.rightEye.scale.y = 1.0 - blinkAmount * 0.8;
            } else {
                this.leftEye.scale.y = 1.0;
                this.rightEye.scale.y = 1.0;
            }
        }
        
        // Update pupil tracking (subtle movement)
        if (this.leftPupil && this.rightPupil) {
            const lookPhase = currentTime * 0.0005;
            this.leftPupil.position.x = Math.sin(lookPhase) * 0.02;
            this.leftPupil.position.y = Math.cos(lookPhase * 0.7) * 0.02;
            this.rightPupil.position.x = Math.sin(lookPhase) * 0.02;
            this.rightPupil.position.y = Math.cos(lookPhase * 0.7) * 0.02;
        }
        
        // Update water particles
        if (this.waterParticles) {
            const positions = this.waterParticles.geometry.attributes.position.array;
            for (let i = 0; i < positions.length; i += 3) {
                // Gentle floating motion
                positions[i + 1] += Math.sin(currentTime * 0.001 + i) * 0.001;
                if (positions[i + 1] > 3) positions[i + 1] = -1;
            }
            this.waterParticles.geometry.attributes.position.needsUpdate = true;
        }
        
        // Update mist particles
        if (this.mistParticles) {
            const positions = this.mistParticles.geometry.attributes.position.array;
            for (let i = 0; i < positions.length; i += 3) {
                positions[i + 1] += deltaTime * 0.2;
                positions[i] += Math.sin(currentTime * 0.001 + i) * 0.01;
                if (positions[i + 1] > 3) {
                    positions[i + 1] = -1;
                    positions[i] = (Math.random() - 0.5) * 4;
                }
            }
            this.mistParticles.geometry.attributes.position.needsUpdate = true;
        }
        
        // Update water group (subtle wave motion)
        if (this.waterGroup) {
            this.waterGroup.children.forEach((plane, index) => {
                const wavePhase = currentTime * 0.0005 + index * 0.5;
                plane.rotation.x = Math.PI / 4 + Math.sin(wavePhase) * 0.05;
                plane.position.y = Math.sin(wavePhase * 1.3) * 0.2;
            });
        }
        
        // Rotate Poseidon slightly for dynamic feel
        if (this.poseidon) {
            this.poseidon.rotation.y = Math.sin(currentTime * 0.0003) * 0.1;
        }
        
        // Update camera (subtle orbit)
        if (this.camera) {
            const cameraOrbit = currentTime * 0.0001;
            this.camera.position.x = Math.sin(cameraOrbit) * 0.5;
            this.camera.position.z = 8 + Math.cos(cameraOrbit) * 0.3;
            this.camera.lookAt(0, 1.5, 0);
        }
        
        // Render
        this.renderer.render(this.scene, this.camera);
        
        this.frameCount++;
    }
    
    onWindowResize() {
        if (!this.container || !this.camera || !this.renderer) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    // Public API
    speak(text, duration) {
        this.startSpeaking(text, duration);
    }
    
    stop() {
        this.stopSpeaking();
    }
    
    setSpeaking(isSpeaking) {
        if (isSpeaking && !this.isSpeaking) {
            // Start speaking animation
        } else if (!isSpeaking && this.isSpeaking) {
            this.stopSpeaking();
        }
    }
    
    // Advanced shader materials and effects
    createAdvancedMaterials() {
        // Subsurface scattering material for skin (advanced)
        this.skinShaderMaterial = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                color: { value: new THREE.Color(this.colors.skin) },
                lightPos: { value: new THREE.Vector3(5, 10, 5) },
                cameraPos: { value: new THREE.Vector3(0, 2, 8) }
            },
            vertexShader: `
                varying vec3 vNormal;
                varying vec3 vWorldPosition;
                varying vec3 vViewPosition;
                
                void main() {
                    vNormal = normalize(normalMatrix * normal);
                    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
                    vWorldPosition = worldPosition.xyz;
                    vViewPosition = cameraPosition - worldPosition.xyz;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 color;
                uniform vec3 lightPos;
                uniform vec3 cameraPos;
                uniform float time;
                
                varying vec3 vNormal;
                varying vec3 vWorldPosition;
                varying vec3 vViewPosition;
                
                void main() {
                    vec3 normal = normalize(vNormal);
                    vec3 lightDir = normalize(lightPos - vWorldPosition);
                    vec3 viewDir = normalize(vViewPosition);
                    
                    // Basic lighting
                    float NdotL = max(dot(normal, lightDir), 0.0);
                    vec3 diffuse = color * NdotL;
                    
                    // Subsurface scattering approximation
                    float rim = 1.0 - max(dot(normal, viewDir), 0.0);
                    vec3 sss = color * rim * rim * 0.5;
                    
                    // Specular
                    vec3 halfDir = normalize(lightDir + viewDir);
                    float spec = pow(max(dot(normal, halfDir), 0.0), 32.0);
                    vec3 specular = vec3(1.0) * spec * 0.3;
                    
                    // Combine
                    vec3 finalColor = diffuse + sss + specular + color * 0.2;
                    gl_FragColor = vec4(finalColor, 1.0);
                }
            `
        });
        
        // Water shader with caustics
        this.waterShaderMaterial = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                color: { value: new THREE.Color(this.colors.water) },
                caustics: { value: 1.0 }
            },
            vertexShader: `
                varying vec3 vPosition;
                varying vec3 vNormal;
                uniform float time;
                
                void main() {
                    vPosition = position;
                    vNormal = normal;
                    vec3 pos = position;
                    pos.y += sin(pos.x * 2.0 + time) * 0.1;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 color;
                uniform float time;
                uniform float caustics;
                varying vec3 vPosition;
                varying vec3 vNormal;
                
                void main() {
                    vec3 normal = normalize(vNormal);
                    float caustic = sin(vPosition.x * 5.0 + time) * sin(vPosition.z * 5.0 + time * 1.3) * 0.5 + 0.5;
                    vec3 finalColor = color * (0.7 + caustic * caustics * 0.3);
                    gl_FragColor = vec4(finalColor, 0.8);
                }
            `,
            transparent: true
        });
        
        // Electric/lightning shader for trident tips
        this.electricShaderMaterial = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                color: { value: new THREE.Color(0x00ffff) },
                intensity: { value: 1.0 }
            },
            vertexShader: `
                varying vec3 vPosition;
                varying vec3 vNormal;
                
                void main() {
                    vPosition = position;
                    vNormal = normal;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform float time;
                uniform vec3 color;
                uniform float intensity;
                varying vec3 vPosition;
                varying vec3 vNormal;
                
                void main() {
                    float pulse = sin(time * 10.0) * 0.5 + 0.5;
                    float flicker = step(0.7, fract(time * 20.0));
                    vec3 finalColor = color * (intensity + pulse * 0.5) * flicker;
                    gl_FragColor = vec4(finalColor, 1.0);
                }
            `,
            blending: THREE.AdditiveBlending
        });
    }
    
    // Advanced facial animation system
    createAdvancedFacialFeatures() {
        // More detailed eyes with iris detail
        if (this.leftEye && this.rightEye) {
            // Add iris rings
            const irisRingGeometry = new THREE.RingGeometry(0.04, 0.055, 32);
            const irisRingMaterial = new THREE.MeshStandardMaterial({
                color: 0x0066cc,
                roughness: 0.3,
                metalness: 0.5
            });
            
            const leftIrisRing = new THREE.Mesh(irisRingGeometry, irisRingMaterial);
            leftIrisRing.position.z = 0.005;
            this.leftEye.add(leftIrisRing);
            
            const rightIrisRing = new THREE.Mesh(irisRingGeometry, irisRingMaterial);
            rightIrisRing.position.z = 0.005;
            this.rightEye.add(rightIrisRing);
            
            // Add eye highlights
            const highlightGeometry = new THREE.SphereGeometry(0.015, 12, 12);
            const highlightMaterial = new THREE.MeshStandardMaterial({
                color: 0xffffff,
                emissive: 0xffffff,
                emissiveIntensity: 0.8,
                roughness: 0.1,
                metalness: 0.9
            });
            
            const leftHighlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
            leftHighlight.position.set(-0.02, 0.02, 0.04);
            this.leftEye.add(leftHighlight);
            
            const rightHighlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
            rightHighlight.position.set(-0.02, 0.02, 0.04);
            this.rightEye.add(rightHighlight);
        }
        
        // Add more facial detail - cheekbones, jawline
        if (this.headMesh) {
            // Cheekbone highlights
            const cheekGeometry = new THREE.SphereGeometry(0.15, 16, 16);
            const cheekMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.skinDark,
                roughness: 0.6,
                transparent: true,
                opacity: 0.3
            });
            cheekGeometry.scale(1, 0.5, 0.3);
            
            const leftCheek = new THREE.Mesh(cheekGeometry, cheekMaterial);
            leftCheek.position.set(-0.25, -0.05, 0.32);
            this.headMesh.add(leftCheek);
            
            const rightCheek = new THREE.Mesh(cheekGeometry, cheekMaterial);
            rightCheek.position.set(0.25, -0.05, 0.32);
            this.headMesh.add(rightCheek);
            
            // Forehead detail
            const foreheadGeometry = new THREE.SphereGeometry(0.35, 16, 16);
            const foreheadMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.skin,
                roughness: 0.7
            });
            foreheadGeometry.scale(1, 0.6, 0.8);
            
            const forehead = new THREE.Mesh(foreheadGeometry, foreheadMaterial);
            forehead.position.set(0, 0.25, -0.15);
            this.headMesh.add(forehead);
        }
    }
    
    // Advanced body musculature
    addAdvancedMusculature() {
        if (!this.body) return;
        
        // Deltoids
        const deltoidGeometry = new THREE.SphereGeometry(0.2, 12, 8);
        const muscleMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skinDark,
            roughness: 0.5
        });
        deltoidGeometry.scale(1, 1, 0.6);
        
        const leftDeltoid = new THREE.Mesh(deltoidGeometry, muscleMaterial);
        leftDeltoid.position.set(-0.5, 2.1, 0.4);
        this.body.add(leftDeltoid);
        
        const rightDeltoid = new THREE.Mesh(deltoidGeometry, muscleMaterial);
        rightDeltoid.position.set(0.5, 2.1, 0.4);
        this.body.add(rightDeltoid);
        
        // Biceps definition
        if (this.leftArm && this.leftArm.children.length > 1) {
            const bicepGeometry = new THREE.CylinderGeometry(0.13, 0.12, 0.3, 12);
            const bicepMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.skinDark,
                roughness: 0.5
            });
            
            const leftBicep = new THREE.Mesh(bicepGeometry, bicepMaterial);
            leftBicep.position.set(-0.7, 1.75, 0.1);
            leftBicep.rotation.z = Math.PI / 6;
            this.leftArm.add(leftBicep);
            
            const rightBicep = new THREE.Mesh(bicepGeometry, bicepMaterial);
            rightBicep.position.set(0.7, 1.75, 0.1);
            rightBicep.rotation.z = -Math.PI / 6;
            this.rightArm.add(rightBicep);
        }
        
        // Latissimus dorsi
        const latGeometry = new THREE.BoxGeometry(0.4, 0.6, 0.1);
        const latMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skinDark,
            roughness: 0.6
        });
        
        const leftLat = new THREE.Mesh(latGeometry, latMaterial);
        leftLat.position.set(-0.4, 1.5, -0.35);
        leftLat.rotation.z = -0.2;
        this.body.add(leftLat);
        
        const rightLat = new THREE.Mesh(latGeometry, latMaterial);
        rightLat.position.set(0.4, 1.5, -0.35);
        rightLat.rotation.z = 0.2;
        this.body.add(rightLat);
        
        // Obliques
        for (let i = 0; i < 3; i++) {
            const obliqueGeometry = new THREE.BoxGeometry(0.15, 0.1, 0.05);
            const obliqueMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.skinDark,
                roughness: 0.5
            });
            
            const leftOblique = new THREE.Mesh(obliqueGeometry, obliqueMaterial);
            leftOblique.position.set(-0.35, 1.1 - i * 0.15, 0.52);
            leftOblique.rotation.z = -0.3;
            this.body.add(leftOblique);
            
            const rightOblique = new THREE.Mesh(obliqueGeometry, obliqueMaterial);
            rightOblique.position.set(0.35, 1.1 - i * 0.15, 0.52);
            rightOblique.rotation.z = 0.3;
            this.body.add(rightOblique);
        }
    }
    
    // Advanced trident effects
    enhanceTrident() {
        if (!this.trident) return;
        
        // Add lightning bolts between prongs
        const lightningGroup = new THREE.Group();
        
        for (let i = 0; i < 10; i++) {
            const points = [];
            const numPoints = 20;
            for (let j = 0; j < numPoints; j++) {
                const t = j / (numPoints - 1);
                const offset = (Math.random() - 0.5) * 0.1;
                points.push(new THREE.Vector3(
                    offset * (1 - t),
                    t * 0.6 - 0.3,
                    (Math.random() - 0.5) * 0.05
                ));
            }
            
            const curve = new THREE.CatmullRomCurve3(points);
            const lightningGeometry = new THREE.TubeGeometry(curve, numPoints, 0.01, 8, false);
            const lightningMaterial = new THREE.MeshStandardMaterial({
                color: 0x00ffff,
                emissive: 0x00ffff,
                emissiveIntensity: 0.8,
                transparent: true,
                opacity: 0.6
            });
            
            const lightning = new THREE.Mesh(lightningGeometry, lightningMaterial);
            lightning.position.set(
                (Math.random() - 0.5) * 0.3,
                2.8,
                (Math.random() - 0.5) * 0.1
            );
            lightningGroup.add(lightning);
        }
        
        this.trident.add(lightningGroup);
        this.tridentLightning = lightningGroup;
        
        // Add energy orb at trident base
        const orbGeometry = new THREE.SphereGeometry(0.15, 16, 16);
        const orbMaterial = new THREE.MeshStandardMaterial({
            color: 0x0088ff,
            emissive: 0x0088ff,
            emissiveIntensity: 1.0,
            transparent: true,
            opacity: 0.8
        });
        const orb = new THREE.Mesh(orbGeometry, orbMaterial);
        orb.position.y = 0.5;
        this.trident.add(orb);
        this.tridentOrb = orb;
    }
    
    // Advanced particle systems
    createAdvancedParticles() {
        // Create bubble particles
        const bubbleGeometry = new THREE.BufferGeometry();
        const bubbleCount = 150;
        const bubblePositions = new Float32Array(bubbleCount * 3);
        const bubbleSizes = new Float32Array(bubbleCount);
        const bubbleSpeeds = new Float32Array(bubbleCount);
        
        for (let i = 0; i < bubbleCount; i++) {
            const i3 = i * 3;
            bubblePositions[i3] = (Math.random() - 0.5) * 6;
            bubblePositions[i3 + 1] = -2 + Math.random() * 4;
            bubblePositions[i3 + 2] = (Math.random() - 0.5) * 6;
            
            bubbleSizes[i] = 0.03 + Math.random() * 0.07;
            bubbleSpeeds[i] = 0.3 + Math.random() * 0.4;
        }
        
        bubbleGeometry.setAttribute('position', new THREE.BufferAttribute(bubblePositions, 3));
        bubbleGeometry.setAttribute('size', new THREE.BufferAttribute(bubbleSizes, 1));
        bubbleGeometry.setAttribute('speed', new THREE.BufferAttribute(bubbleSpeeds, 1));
        
        const bubbleMaterial = new THREE.PointsMaterial({
            color: 0xa0e0ff,
            size: 0.08,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });
        
        this.bubbleParticles = new THREE.Points(bubbleGeometry, bubbleMaterial);
        this.scene.add(this.bubbleParticles);
        
        // Create sparkle particles (for magical effect)
        const sparkleGeometry = new THREE.BufferGeometry();
        const sparkleCount = 100;
        const sparklePositions = new Float32Array(sparkleCount * 3);
        const sparkleColors = new Float32Array(sparkleCount * 3);
        const sparkleSizes = new Float32Array(sparkleCount);
        const sparkleLifetimes = new Float32Array(sparkleCount);
        
        for (let i = 0; i < sparkleCount; i++) {
            const i3 = i * 3;
            const radius = 3 + Math.random() * 2;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;
            
            sparklePositions[i3] = Math.sin(phi) * Math.cos(theta) * radius;
            sparklePositions[i3 + 1] = Math.cos(phi) * radius + 1;
            sparklePositions[i3 + 2] = Math.sin(phi) * Math.sin(theta) * radius;
            
            const color = new THREE.Color().setHSL(0.55 + Math.random() * 0.1, 1.0, 0.5 + Math.random() * 0.3);
            sparkleColors[i3] = color.r;
            sparkleColors[i3 + 1] = color.g;
            sparkleColors[i3 + 2] = color.b;
            
            sparkleSizes[i] = 0.05 + Math.random() * 0.1;
            sparkleLifetimes[i] = Math.random();
        }
        
        sparkleGeometry.setAttribute('position', new THREE.BufferAttribute(sparklePositions, 3));
        sparkleGeometry.setAttribute('color', new THREE.BufferAttribute(sparkleColors, 3));
        sparkleGeometry.setAttribute('size', new THREE.BufferAttribute(sparkleSizes, 1));
        sparkleGeometry.setAttribute('lifetime', new THREE.BufferAttribute(sparkleLifetimes, 1));
        
        const sparkleMaterial = new THREE.PointsMaterial({
            size: 0.15,
            transparent: true,
            opacity: 0.8,
            vertexColors: true,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });
        
        this.sparkleParticles = new THREE.Points(sparkleGeometry, sparkleMaterial);
        this.scene.add(this.sparkleParticles);
    }
    
    // Enhanced lip-sync with viseme system
    updateAdvancedLipSync(phoneme, intensity, deltaTime) {
        if (!this.mouth || !this.mouthOpening) return;
        
        // Advanced viseme shapes
        const visemeShapes = {
            'A': { open: 0.8, wide: 0.3, protrude: 0.0 },
            'E': { open: 0.6, wide: 0.6, protrude: 0.0 },
            'I': { open: 0.4, wide: 0.8, protrude: 0.0 },
            'O': { open: 0.9, wide: 0.1, protrude: 0.4 },
            'U': { open: 0.7, wide: 0.0, protrude: 0.6 },
            'M': { open: 0.2, wide: 0.0, protrude: 0.0 },
            'P': { open: 0.3, wide: 0.0, protrude: 0.2 },
            'B': { open: 0.3, wide: 0.0, protrude: 0.2 },
            'F': { open: 0.4, wide: 0.2, protrude: 0.0 },
            'V': { open: 0.4, wide: 0.2, protrude: 0.0 },
            'TH': { open: 0.3, wide: 0.1, protrude: 0.3 },
            'S': { open: 0.2, wide: 0.4, protrude: 0.0 },
            'Z': { open: 0.2, wide: 0.4, protrude: 0.0 },
            'SH': { open: 0.3, wide: 0.5, protrude: 0.2 },
            'CH': { open: 0.4, wide: 0.3, protrude: 0.3 },
            'L': { open: 0.3, wide: 0.0, protrude: 0.4 },
            'R': { open: 0.4, wide: 0.2, protrude: 0.3 },
            'T': { open: 0.2, wide: 0.1, protrude: 0.2 },
            'D': { open: 0.3, wide: 0.1, protrude: 0.3 },
            'N': { open: 0.3, wide: 0.0, protrude: 0.2 },
            'K': { open: 0.2, wide: 0.0, protrude: 0.0 },
            'G': { open: 0.3, wide: 0.0, protrude: 0.0 },
            'Y': { open: 0.5, wide: 0.6, protrude: 0.1 },
            'W': { open: 0.6, wide: 0.0, protrude: 0.5 },
            'H': { open: 0.5, wide: 0.2, protrude: 0.0 },
            'silence': { open: 0.0, wide: 0.0, protrude: 0.0 }
        };
        
        const targetShape = visemeShapes[phoneme] || visemeShapes['silence'];
        const lerpSpeed = 15.0 * deltaTime;
        
        this.mouthOpenness = THREE.MathUtils.lerp(
            this.mouthOpenness,
            targetShape.open * intensity,
            lerpSpeed
        );
        
        // Apply viseme shape
        this.mouthOpening.scale.y = this.mouthOpenness;
        this.mouthOpening.scale.x = 1.0 + targetShape.wide * intensity;
        this.mouthOpening.scale.z = 1.0 + targetShape.protrude * intensity;
        
        // Animate individual lip components
        if (this.upperLip && this.lowerLip) {
            this.upperLip.position.y = 0.01 + this.mouthOpenness * 0.05;
            this.lowerLip.position.y = -0.01 - this.mouthOpenness * 0.05;
            this.upperLip.scale.x = 1.0 + targetShape.wide * 0.3;
            this.lowerLip.scale.x = 1.0 + targetShape.wide * 0.3;
        }
        
        if (this.mouthBase) {
            this.mouthBase.scale.y = 1.0 - this.mouthOpenness * 0.8;
            this.mouthBase.scale.x = 1.0 + targetShape.wide * 0.2;
        }
        
        if (this.mouthInterior) {
            this.mouthInterior.scale.y = this.mouthOpenness;
            this.mouthInterior.scale.x = 1.0 + targetShape.wide * 0.2;
            this.mouthInterior.position.z = 0.02 + targetShape.protrude * 0.03;
        }
    }
    
    // Advanced animation system with state machine
    updateAdvancedAnimations(deltaTime, currentTime) {
        // Breathing with more realism
        this.breathePhase += deltaTime * this.breatheSpeed;
        const breathePattern = Math.sin(this.breathePhase) * 0.5 + 
                              Math.sin(this.breathePhase * 2) * 0.3 +
                              Math.sin(this.breathePhase * 0.5) * 0.2;
        const breatheOffset = breathePattern * this.breatheAmplitude;
        
        if (this.body) {
            this.body.scale.y = 1.0 + breatheOffset;
            this.body.scale.x = 1.0 - breatheOffset * 0.3;
        }
        
        // Chest expansion
        if (this.body) {
            this.body.scale.z = 1.0 + breatheOffset * 0.5;
        }
        
        // Advanced head movement
        this.headBob += deltaTime * 0.3;
        const headMovement = Math.sin(this.headBob) * 0.02;
        const headRotation = Math.sin(this.headBob * 0.5) * 0.05;
        const headTilt = Math.cos(this.headBob * 0.7) * 0.02;
        
        if (this.head) {
            this.head.position.y = 2.2 + headMovement;
            this.head.rotation.y = headRotation;
            this.head.rotation.z = headTilt;
        }
        
        // Micro-expressions on face
        if (this.headMesh) {
            const microExpression = Math.sin(currentTime * 0.002) * 0.01;
            this.headMesh.scale.x = 1.0 + microExpression;
            this.headMesh.scale.y = 1.0 - microExpression * 0.5;
        }
        
        // Advanced trident animation
        if (this.trident) {
            this.tridentSway += deltaTime * 0.4;
            const swayAmount = Math.sin(this.tridentSway) * 0.05;
            const rotationAmount = Math.cos(this.tridentSway * 0.7) * 0.03;
            
            this.trident.rotation.z = Math.PI / 6 + swayAmount;
            this.trident.rotation.y = -Math.PI / 4 + rotationAmount;
            this.trident.rotation.x = Math.sin(this.tridentSway * 0.5) * 0.02;
            
            // Pulse animation for trident
            const tridentPulse = Math.sin(currentTime * 0.005) * 0.02 + 1.0;
            this.trident.scale.set(tridentPulse, tridentPulse, tridentPulse);
            
            // Animate trident tips with advanced effects
            if (this.tridentProngs) {
                const electricPhase = currentTime * 0.01;
                this.tridentProngs.children.forEach((prong, index) => {
                    if (prong.type === 'Mesh' && prong.material && prong.material.emissive) {
                        const intensity = 0.5 + Math.sin(electricPhase + index * 2) * 0.5;
                        prong.material.emissiveIntensity = intensity;
                        
                        // Add subtle rotation
                        prong.rotation.z = Math.sin(electricPhase + index) * 0.1;
                    }
                });
            }
            
            // Animate trident orb
            if (this.tridentOrb) {
                const orbPulse = Math.sin(currentTime * 0.008) * 0.3 + 1.0;
                this.tridentOrb.scale.set(orbPulse, orbPulse, orbPulse);
                this.tridentOrb.rotation.y += deltaTime * 2.0;
                this.tridentOrb.rotation.x += deltaTime * 1.5;
                
                if (this.tridentOrb.material) {
                    this.tridentOrb.material.emissiveIntensity = 0.8 + Math.sin(currentTime * 0.01) * 0.4;
                }
            }
            
            // Animate lightning between prongs
            if (this.tridentLightning) {
                this.tridentLightning.children.forEach((lightning, index) => {
                    lightning.rotation.y += deltaTime * (1 + index * 0.1);
                    if (lightning.material) {
                        lightning.material.opacity = 0.4 + Math.sin(currentTime * 0.02 + index) * 0.3;
                        lightning.material.emissiveIntensity = 0.6 + Math.sin(currentTime * 0.015 + index) * 0.4;
                    }
                });
            }
        }
        
        // Advanced eye animation
        if (this.leftEye && this.rightEye) {
            // Blinking with more realism
            const blinkPhase = Math.sin(currentTime * 0.001);
            if (blinkPhase > 0.95 || blinkPhase < -0.95) {
                const blinkAmount = Math.abs(blinkPhase) > 0.95 ? 
                    (Math.abs(blinkPhase) - 0.95) * 20 : 0;
                this.leftEye.scale.y = 1.0 - blinkAmount * 0.8;
                this.rightEye.scale.y = 1.0 - blinkAmount * 0.8;
            } else {
                this.leftEye.scale.y = 1.0;
                this.rightEye.scale.y = 1.0;
            }
            
            // Eye movement (looking around)
            const lookPhase = currentTime * 0.0005;
            const lookX = Math.sin(lookPhase) * 0.02;
            const lookY = Math.cos(lookPhase * 0.7) * 0.02;
            
            if (this.leftPupil) {
                this.leftPupil.position.x = lookX;
                this.leftPupil.position.y = lookY;
            }
            if (this.rightPupil) {
                this.rightPupil.position.x = lookX;
                this.rightPupil.position.y = lookY;
            }
            
            // Eye dilation based on emotion/speaking
            const eyeScale = this.isSpeaking ? 1.1 : 1.0;
            this.leftEye.scale.x = eyeScale;
            this.leftEye.scale.z = eyeScale;
            this.rightEye.scale.x = eyeScale;
            this.rightEye.scale.z = eyeScale;
        }
        
        // Update bubble particles
        if (this.bubbleParticles) {
            const positions = this.bubbleParticles.geometry.attributes.position.array;
            const speeds = this.bubbleParticles.geometry.attributes.speed.array;
            
            for (let i = 0; i < positions.length; i += 3) {
                positions[i + 1] += speeds[i / 3] * deltaTime;
                
                // Add slight horizontal drift
                positions[i] += Math.sin(currentTime * 0.001 + i) * 0.01 * deltaTime;
                positions[i + 2] += Math.cos(currentTime * 0.001 + i) * 0.01 * deltaTime;
                
                // Reset if too high
                if (positions[i + 1] > 3) {
                    positions[i + 1] = -2;
                    positions[i] = (Math.random() - 0.5) * 6;
                    positions[i + 2] = (Math.random() - 0.5) * 6;
                }
            }
            
            this.bubbleParticles.geometry.attributes.position.needsUpdate = true;
        }
        
        // Update sparkle particles
        if (this.sparkleParticles) {
            const positions = this.sparkleParticles.geometry.attributes.position.array;
            const lifetimes = this.sparkleParticles.geometry.attributes.lifetime.array;
            
            for (let i = 0; i < positions.length; i += 3) {
                lifetimes[i / 3] += deltaTime * 0.5;
                if (lifetimes[i / 3] > 1.0) {
                    lifetimes[i / 3] = 0;
                    const radius = 3 + Math.random() * 2;
                    const theta = Math.random() * Math.PI * 2;
                    const phi = Math.random() * Math.PI;
                    positions[i] = Math.sin(phi) * Math.cos(theta) * radius;
                    positions[i + 1] = Math.cos(phi) * radius + 1;
                    positions[i + 2] = Math.sin(phi) * Math.sin(theta) * radius;
                }
                
                // Sparkle movement
                positions[i + 1] += Math.sin(lifetimes[i / 3] * Math.PI * 2) * 0.02 * deltaTime;
            }
            
            this.sparkleParticles.geometry.attributes.position.needsUpdate = true;
            this.sparkleParticles.geometry.attributes.lifetime.needsUpdate = true;
        }
        
        // Advanced water group animation
        if (this.waterGroup) {
            this.waterGroup.children.forEach((plane, index) => {
                const wavePhase = currentTime * 0.0005 + index * 0.5;
                const waveAmplitude = 0.05 + index * 0.02;
                plane.rotation.x = Math.PI / 4 + Math.sin(wavePhase) * waveAmplitude;
                plane.rotation.z = Math.sin(wavePhase * 1.3) * 0.03;
                plane.position.y = Math.sin(wavePhase * 1.3) * 0.2;
                plane.position.x = Math.cos(wavePhase * 0.8) * 0.1;
                
                // Update opacity for depth
                if (plane.material) {
                    plane.material.opacity = 0.1 - index * 0.015 + Math.sin(wavePhase) * 0.02;
                }
            });
        }
        
        // Poseidon rotation with breathing rhythm
        if (this.poseidon) {
            const rotationPhase = currentTime * 0.0003;
            this.poseidon.rotation.y = Math.sin(rotationPhase) * 0.1;
            this.poseidon.rotation.z = Math.sin(rotationPhase * 0.7) * 0.02;
        }
        
        // Advanced camera movement
        if (this.camera) {
            const cameraOrbit = currentTime * 0.0001;
            const cameraBob = Math.sin(currentTime * 0.0008) * 0.2;
            
            this.camera.position.x = Math.sin(cameraOrbit) * 0.5;
            this.camera.position.y = 2 + cameraBob;
            this.camera.position.z = 8 + Math.cos(cameraOrbit) * 0.3;
            
            // Smooth camera look-at with slight lead
            const targetLookY = 1.5 + Math.sin(currentTime * 0.0005) * 0.1;
            this.camera.lookAt(0, targetLookY, 0);
        }
        
        // Update shader uniforms
        if (this.skinShaderMaterial) {
            this.skinShaderMaterial.uniforms.time.value = currentTime;
            if (this.mainLight) {
                this.skinShaderMaterial.uniforms.lightPos.value.copy(this.mainLight.position);
            }
            if (this.camera) {
                this.skinShaderMaterial.uniforms.cameraPos.value.copy(this.camera.position);
            }
        }
        
        if (this.waterShaderMaterial) {
            this.waterShaderMaterial.uniforms.time.value = currentTime;
        }
        
        if (this.electricShaderMaterial) {
            this.electricShaderMaterial.uniforms.time.value = currentTime;
            this.electricShaderMaterial.uniforms.intensity.value = 
                this.isSpeaking ? 1.5 : 1.0;
        }
        
        // Update advanced features
        this.updateHairPhysics(deltaTime, currentTime);
        this.updateClothSimulation(deltaTime, currentTime);
        this.updateAdvancedLighting(currentTime);
        this.updateWaterSurface(currentTime);
        
        // Update caustics
        if (this.causticsGroup) {
            this.causticsGroup.children.forEach((caustic, index) => {
                const phase = currentTime + index * 0.5;
                caustic.rotation.z += deltaTime * 0.1;
                if (caustic.material) {
                    caustic.material.opacity = 0.08 + Math.sin(phase) * 0.04;
                }
            });
        }
        
        // Update all new advanced systems (comprehensive)
        if (this.updateFacialExpression) this.updateFacialExpression(deltaTime);
        if (this.updateIKSystem) this.updateIKSystem(deltaTime, currentTime);
        if (this.updateWaterRipples) this.updateWaterRipples(deltaTime);
        if (this.updateParticleTrail) this.updateParticleTrail(deltaTime);
        if (this.updateDepthOfField) this.updateDepthOfField(currentTime);
        if (this.blendAnimations) this.blendAnimations(deltaTime);
        if (this.updateMuscleFlex) this.updateMuscleFlex(deltaTime);
        if (this.updateGestures) this.updateGestures(deltaTime);
        if (this.updateEyeTracking) this.updateEyeTracking(deltaTime);
        if (this.updateReflectionSystem) this.updateReflectionSystem(currentTime);
        if (this.updateBreathingSystem) this.updateBreathingSystem(deltaTime);
        if (this.updateWaterDetail) this.updateWaterDetail(currentTime);
        if (this.updateMotionBlur) this.updateMotionBlur(deltaTime);
        if (this.updateMaterialStates) this.updateMaterialStates(currentTime);
        if (this.updateCulling) this.updateCulling();
        
        // Set facial expression based on state
        if (this.setFacialExpression) {
            if (this.isSpeaking) {
                this.setFacialExpression('speaking', 0.8);
            } else {
                this.setFacialExpression('neutral', 1.0);
            }
        }
        
        // Set gestures based on speaking
        if (this.setGesture) {
            if (this.isSpeaking) {
                this.setGesture('left', 'pointing');
            } else {
                this.setGesture('left', 'idle');
            }
        }
        
        // Update eye target to look at camera
        if (this.setEyeTarget && this.camera) {
            this.setEyeTarget(this.camera.position);
        }
    }
    
    // Override animate method with advanced animations
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        const currentTime = performance.now();
        const deltaTime = (currentTime - this.lastFrameTime) / 1000;
        this.lastFrameTime = currentTime;
        const currentTimeSeconds = currentTime / 1000;
        
        // Update advanced animations
        this.updateAdvancedAnimations(deltaTime, currentTimeSeconds);
        
        // Update lip-sync if speaking
        if (this.isSpeaking) {
            this.speechTime += deltaTime;
            this.phonemeTime += deltaTime;
            
            if (this.phonemeTime >= this.phonemeDuration && this.phonemeIndex < this.speechPhonemes.length - 1) {
                this.phonemeIndex++;
                this.phonemeTime = 0;
            }
            
            const currentPhoneme = this.speechPhonemes[this.phonemeIndex] || 'silence';
            const progress = this.phonemeTime / this.phonemeDuration;
            const intensity = 1.0 - Math.abs(progress - 0.5) * 2;
            
            this.updateAdvancedLipSync(currentPhoneme, intensity, deltaTime);
        } else {
            this.updateAdvancedLipSync('silence', 1.0, deltaTime);
        }
        
        // Update performance monitoring
        if (this.updatePerformanceMonitoring) {
            this.updatePerformanceMonitoring(deltaTime);
        }
        
        // Render
        this.renderer.render(this.scene, this.camera);
        
        this.frameCount++;
    }
    
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        // Clean up Three.js resources
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.container && this.renderer && this.renderer.domElement) {
            this.container.removeChild(this.renderer.domElement);
        }
        
        // Dispose geometries and materials
        this.scene.traverse((object) => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach(m => m.dispose());
                } else {
                    object.material.dispose();
                }
            }
        });
        
        window.removeEventListener('resize', () => this.onWindowResize());
    }
    
    // Initialize after DOM is ready and enhance creation methods
    createPoseidon() {
    const poseidonGroup = new THREE.Group();
    
    // Body (torso) - call original
    const bodyGeometry = new THREE.CylinderGeometry(0.6, 0.8, 1.8, 16);
    const bodyMaterial = new THREE.MeshStandardMaterial({
        color: this.colors.skin,
        roughness: 0.7,
        metalness: 0.1
    });
    this.body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    this.body.position.y = 0.9;
    this.body.castShadow = true;
    this.body.receiveShadow = true;
    poseidonGroup.add(this.body);
    
    // Add muscle definition to body
    this.addBodyDetails();
    this.addAdvancedMusculature();
    
    // Head
    this.createHead();
    this.head.position.y = 2.2;
    poseidonGroup.add(this.head);
    this.createAdvancedFacialFeatures();
    
    // Arms
    this.createArms();
    poseidonGroup.add(this.arms);
    
    // Legs
    this.createLegs();
    poseidonGroup.add(this.legs);
    
    // Robe/cloak
    this.createRobe();
    poseidonGroup.add(this.robeGroup);
    
    poseidonGroup.position.y = 0;
    this.scene.add(poseidonGroup);
    this.poseidon = poseidonGroup;
    
    // Create advanced materials after initial setup
    this.createAdvancedMaterials();
    this.createAdvancedParticles();
    this.enhanceTrident();
    }
    
    // Additional advanced features and optimizations
    
    // Advanced environment details
    createAdvancedEnvironment() {
        // Add underwater caustics effect
        const causticsGroup = new THREE.Group();
        for (let i = 0; i < 10; i++) {
            const causticGeometry = new THREE.PlaneGeometry(3, 3, 32, 32);
            const causticPositions = causticGeometry.attributes.position;
            
            for (let j = 0; j < causticPositions.count; j++) {
                const x = causticPositions.getX(j);
                const y = causticPositions.getY(j);
                const causticWave = Math.sin(x * 3 + i) * Math.cos(y * 3 + i) * 0.1;
                causticPositions.setZ(j, causticWave);
            }
            causticGeometry.computeVertexNormals();
            
            const causticMaterial = new THREE.MeshStandardMaterial({
                color: 0x00ffff,
                transparent: true,
                opacity: 0.1,
                side: THREE.DoubleSide,
                emissive: 0x00ffff,
                emissiveIntensity: 0.2
            });
            
            const causticPlane = new THREE.Mesh(causticGeometry, causticMaterial);
            causticPlane.rotation.x = -Math.PI / 2;
            causticPlane.position.y = -0.3 - i * 0.5;
            causticPlane.position.x = (Math.random() - 0.5) * 2;
            causticPlane.position.z = (Math.random() - 0.5) * 2;
            causticsGroup.add(causticPlane);
        }
        this.scene.add(causticsGroup);
        this.causticsGroup = causticsGroup;
    }
    
    // Enhanced muscle detail system
    createMuscleDetailSystem() {
        if (!this.body) return;
        
        // Create muscle fiber detail using displacement
        const muscleDetailGeometry = new THREE.IcosahedronGeometry(0.1, 1);
        const muscleDetailMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skinDark,
            roughness: 0.4,
            metalness: 0.2
        });
        
        // Add muscle fiber details to various body parts
        const musclePositions = [
            { x: -0.2, y: 2.0, z: 0.5, scale: 0.8 }, // Left pec
            { x: 0.2, y: 2.0, z: 0.5, scale: 0.8 },  // Right pec
            { x: 0, y: 1.8, z: 0.55, scale: 0.6 },   // Upper abs
            { x: 0, y: 1.6, z: 0.55, scale: 0.6 },   // Mid abs
            { x: 0, y: 1.4, z: 0.55, scale: 0.6 },   // Lower abs
        ];
        
        musclePositions.forEach(pos => {
            const muscleDetail = new THREE.Mesh(muscleDetailGeometry, muscleDetailMaterial);
            muscleDetail.position.set(pos.x, pos.y, pos.z);
            muscleDetail.scale.setScalar(pos.scale);
            this.body.add(muscleDetail);
        });
    }
    
    // Advanced hair physics simulation
    createHairPhysics() {
        if (!this.hair) return;
        
        // Add individual hair strands with physics
        const hairStrandGeometry = new THREE.CylinderGeometry(0.005, 0.005, 0.3, 6);
        const hairStrandMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.hair,
            roughness: 0.8,
            metalness: 0.1
        });
        
        for (let i = 0; i < 50; i++) {
            const strand = new THREE.Mesh(hairStrandGeometry, hairStrandMaterial);
            const angle = (i / 50) * Math.PI * 2;
            const radius = 0.35 + Math.random() * 0.1;
            strand.position.set(
                Math.cos(angle) * radius * 0.8,
                0.2 + Math.random() * 0.2,
                -0.1 + Math.sin(angle) * radius * 0.5
            );
            strand.rotation.z = angle + (Math.random() - 0.5) * 0.5;
            strand.rotation.y = (Math.random() - 0.5) * 0.3;
            this.hair.add(strand);
        }
        
        this.hairStrands = this.hair.children.filter(child => child.type === 'Mesh');
    }
    
    // Update hair physics
    updateHairPhysics(deltaTime, currentTime) {
        if (!this.hairStrands || this.hairStrands.length === 0) return;
        
        const windStrength = Math.sin(currentTime * 0.5) * 0.1;
        const gravity = 0.5;
        
        this.hairStrands.forEach((strand, index) => {
            const phase = currentTime * 2 + index * 0.1;
            strand.rotation.z += Math.sin(phase) * windStrength * deltaTime;
            strand.rotation.y += Math.cos(phase * 0.7) * windStrength * 0.5 * deltaTime;
            strand.position.y += Math.sin(phase) * 0.01 * deltaTime;
        });
    }
    
    // Advanced cloth simulation for robe
    createClothSimulation() {
        if (!this.robeGroup) return;
        
        // Create cloth-like geometry with more vertices for simulation
        const clothGeometry = new THREE.PlaneGeometry(1.2, 1.8, 20, 30);
        const clothPositions = clothGeometry.attributes.position;
        this.clothOriginalPositions = new Float32Array(clothPositions.array.length);
        this.clothOriginalPositions.set(clothPositions.array);
        this.clothVelocities = new Float32Array(clothPositions.count * 3);
        
        this.clothGeometry = clothGeometry;
    }
    
    // Update cloth simulation
    updateClothSimulation(deltaTime, currentTime) {
        if (!this.clothGeometry || !this.clothOriginalPositions) return;
        
        const positions = this.clothGeometry.attributes.position.array;
        const velocities = this.clothVelocities;
        const gravity = -0.5;
        const damping = 0.95;
        const stiffness = 0.1;
        
        // Simple cloth physics simulation
        for (let i = 0; i < positions.length; i += 3) {
            // Apply gravity
            velocities[i + 1] += gravity * deltaTime;
            
            // Apply damping
            velocities[i] *= damping;
            velocities[i + 1] *= damping;
            velocities[i + 2] *= damping;
            
            // Update positions
            positions[i] += velocities[i] * deltaTime;
            positions[i + 1] += velocities[i + 1] * deltaTime;
            positions[i + 2] += velocities[i + 2] * deltaTime;
            
            // Restore towards original position (spring simulation)
            const originalX = this.clothOriginalPositions[i];
            const originalY = this.clothOriginalPositions[i + 1];
            const originalZ = this.clothOriginalPositions[i + 2];
            
            velocities[i] += (originalX - positions[i]) * stiffness * deltaTime;
            velocities[i + 1] += (originalY - positions[i + 1]) * stiffness * deltaTime;
            velocities[i + 2] += (originalZ - positions[i + 2]) * stiffness * deltaTime;
            
            // Add wind effect
            const windX = Math.sin(currentTime + i * 0.1) * 0.1;
            const windZ = Math.cos(currentTime + i * 0.1) * 0.1;
            velocities[i] += windX * deltaTime;
            velocities[i + 2] += windZ * deltaTime;
        }
        
        this.clothGeometry.computeVertexNormals();
        this.clothGeometry.attributes.position.needsUpdate = true;
    }
    
    // Advanced lighting system with multiple light sources
    enhanceLightingSystem() {
        // Add rim lighting for better character definition
        const rimLight2 = new THREE.DirectionalLight(0x0088ff, 0.5);
        rimLight2.position.set(-3, 1, -8);
        this.scene.add(rimLight2);
        this.rimLight2 = rimLight2;
        
        // Add accent lights for dramatic effect
        const accentLight1 = new THREE.PointLight(0x00d4ff, 0.8, 15);
        accentLight1.position.set(3, 3, 3);
        this.scene.add(accentLight1);
        this.accentLight1 = accentLight1;
        
        const accentLight2 = new THREE.PointLight(0x0088ff, 0.6, 12);
        accentLight2.position.set(-3, 2, 4);
        this.scene.add(accentLight2);
        this.accentLight2 = accentLight2;
        
        // Add volumetric light effect (using helper spheres)
        const volumetricLightGeometry = new THREE.SphereGeometry(0.3, 16, 16);
        const volumetricLightMaterial = new THREE.MeshStandardMaterial({
            color: 0x00bfff,
            emissive: 0x00bfff,
            emissiveIntensity: 2.0,
            transparent: true,
            opacity: 0.3
        });
        
        const volumetricLight = new THREE.Mesh(volumetricLightGeometry, volumetricLightMaterial);
        volumetricLight.position.copy(this.mainLight.position);
        this.scene.add(volumetricLight);
        this.volumetricLight = volumetricLight;
    }
    
    // Update advanced lighting
    updateAdvancedLighting(currentTime) {
        // Animate volumetric light
        if (this.volumetricLight && this.mainLight) {
            this.volumetricLight.position.copy(this.mainLight.position);
            const pulse = Math.sin(currentTime * 0.5) * 0.2 + 1.0;
            this.volumetricLight.scale.setScalar(pulse);
            if (this.volumetricLight.material) {
                this.volumetricLight.material.emissiveIntensity = 1.5 + Math.sin(currentTime * 0.8) * 0.5;
            }
        }
        
        // Animate accent lights
        if (this.accentLight1) {
            const intensity1 = 0.6 + Math.sin(currentTime * 0.7) * 0.3;
            this.accentLight1.intensity = intensity1;
        }
        
        if (this.accentLight2) {
            const intensity2 = 0.4 + Math.cos(currentTime * 0.9) * 0.2;
            this.accentLight2.intensity = intensity2;
        }
        
        // Update water light position
        if (this.waterLight && this.poseidon) {
            this.waterLight.position.y = Math.sin(currentTime * 0.3) * 0.5;
            const waterIntensity = 1.2 + Math.sin(currentTime * 0.5) * 0.3;
            this.waterLight.intensity = waterIntensity;
        }
    }
    
    // Advanced post-processing effects (if supported)
    setupPostProcessing() {
        // Note: Full post-processing requires additional libraries
        // This is a placeholder for future enhancement
        
        // Add glow effect to emissive materials (already handled in materials)
        // Could add bloom, DOF, SSAO, etc. with Three.js post-processing
        
        // For now, enhance materials with better emissive properties
        this.scene.traverse((object) => {
            if (object.material && object.material.emissive) {
                // Enhance emissive materials
                if (object.material.emissiveIntensity === undefined) {
                    object.material.emissiveIntensity = 1.0;
                }
            }
        });
    }
    
    // Enhanced character details
    addCharacterDetails() {
        // Add veins to body (subtle)
        const veinGeometry = new THREE.CylinderGeometry(0.005, 0.005, 0.2, 8);
        const veinMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a5490,
            roughness: 0.8
        });
        
        // Add veins to arms
        if (this.leftArm) {
            for (let i = 0; i < 3; i++) {
                const vein = new THREE.Mesh(veinGeometry, veinMaterial);
                vein.position.set(-0.7, 1.5 - i * 0.2, 0.15);
                vein.rotation.z = Math.PI / 6;
                this.leftArm.add(vein);
            }
        }
        
        if (this.rightArm) {
            for (let i = 0; i < 3; i++) {
                const vein = new THREE.Mesh(veinGeometry, veinMaterial);
                vein.position.set(0.7, 1.5 - i * 0.2, 0.15);
                vein.rotation.z = -Math.PI / 6;
                this.rightArm.add(vein);
            }
        }
        
        // Add finger details
        if (this.leftHand) {
            this.leftHand.children.forEach((finger, index) => {
                if (finger.type === 'Mesh' && index > 0) {
                    // Add finger joints
                    const jointGeometry = new THREE.SphereGeometry(0.01, 8, 8);
                    const jointMaterial = new THREE.MeshStandardMaterial({
                        color: this.colors.skinDark,
                        roughness: 0.6
                    });
                    
                    const joint = new THREE.Mesh(jointGeometry, jointMaterial);
                    joint.position.set(0, -0.03, 0);
                    finger.add(joint);
                }
            });
        }
        
        // Add toenails to feet
        if (this.legs) {
            this.legs.children.forEach(leg => {
                leg.children.forEach(foot => {
                    if (foot.type === 'Mesh' && foot.position.y < -0.8) {
                        const toenailGeometry = new THREE.BoxGeometry(0.02, 0.01, 0.03);
                        const toenailMaterial = new THREE.MeshStandardMaterial({
                            color: 0x1a1a2e,
                            roughness: 0.9
                        });
                        
                        for (let i = 0; i < 5; i++) {
                            const toenail = new THREE.Mesh(toenailGeometry, toenailMaterial);
                            toenail.position.set(
                                (i - 2) * 0.03,
                                -0.02,
                                0.12
                            );
                            foot.add(toenail);
                        }
                    }
                });
            });
        }
    }
    
    // Enhanced trident details
    addTridentDetails() {
        if (!this.trident) return;
        
        // Add decorative elements to trident shaft
        const decorationGeometry = new THREE.TorusGeometry(0.045, 0.005, 8, 16);
        const decorationMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.tridentGold,
            roughness: 0.2,
            metalness: 1.0,
            emissive: this.colors.tridentGold,
            emissiveIntensity: 0.3
        });
        
        for (let i = 0; i < 8; i++) {
            const decoration = new THREE.Mesh(decorationGeometry, decorationMaterial);
            decoration.position.y = 0.5 + i * 0.25;
            decoration.rotation.x = Math.PI / 2;
            this.trident.add(decoration);
        }
        
        // Add runes or symbols to trident (using simple geometry)
        const runeGeometry = new THREE.BoxGeometry(0.02, 0.08, 0.01);
        const runeMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.tridentGold,
            emissive: this.colors.tridentGold,
            emissiveIntensity: 0.5
        });
        
        for (let i = 0; i < 6; i++) {
            const rune = new THREE.Mesh(runeGeometry, runeMaterial);
            rune.position.set(
                0.05,
                0.8 + i * 0.3,
                0
            );
            rune.rotation.y = (i % 2) * Math.PI / 4;
            this.trident.add(rune);
        }
    }
    
    // Advanced water surface with ripples
    createWaterSurface() {
        const waterSurfaceGeometry = new THREE.PlaneGeometry(20, 20, 64, 64);
        const waterPositions = waterSurfaceGeometry.attributes.position;
        
        // Create initial wave pattern
        for (let i = 0; i < waterPositions.count; i++) {
            const x = waterPositions.getX(i);
            const y = waterPositions.getY(i);
            const distance = Math.sqrt(x * x + y * y);
            const wave = Math.sin(distance * 0.5) * 0.3;
            waterPositions.setZ(i, wave);
        }
        
        waterSurfaceGeometry.computeVertexNormals();
        
        const waterSurfaceMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.water,
            transparent: true,
            opacity: 0.6,
            roughness: 0.1,
            metalness: 0.8,
            side: THREE.DoubleSide,
            emissive: this.colors.water,
            emissiveIntensity: 0.2
        });
        
        const waterSurface = new THREE.Mesh(waterSurfaceGeometry, waterSurfaceMaterial);
        waterSurface.rotation.x = -Math.PI / 2;
        waterSurface.position.y = -0.3;
        waterSurface.receiveShadow = true;
        this.scene.add(waterSurface);
        this.waterSurface = waterSurface;
    }
    
    // Update water surface animation
    updateWaterSurface(currentTime) {
        if (!this.waterSurface) return;
        
        const positions = this.waterSurface.geometry.attributes.position;
        
        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const y = positions.getY(i);
            const distance = Math.sqrt(x * x + y * y);
            
            // Multiple wave frequencies for realistic water
            const wave1 = Math.sin(distance * 0.5 - currentTime * 0.5) * 0.3;
            const wave2 = Math.sin(distance * 1.2 - currentTime * 0.8) * 0.15;
            const wave3 = Math.sin(x * 2 - currentTime * 1.2) * Math.cos(y * 2 - currentTime * 1.0) * 0.1;
            
            positions.setZ(i, wave1 + wave2 + wave3);
        }
        
        this.waterSurface.geometry.computeVertexNormals();
        this.waterSurface.geometry.attributes.position.needsUpdate = true;
    }
    
    
    // Advanced facial animation system with expressions
    createFacialExpressionSystem() {
        // Store base positions for facial features
        this.facialExpressions = {
            neutral: {
                eyebrowY: 0.18,
                eyebrowRotation: 0,
                eyeScale: 1.0,
                mouthCurve: 0
            },
            happy: {
                eyebrowY: 0.20,
                eyebrowRotation: -0.1,
                eyeScale: 0.9,
                mouthCurve: 0.3
            },
            angry: {
                eyebrowY: 0.16,
                eyebrowRotation: 0.3,
                eyeScale: 1.1,
                mouthCurve: -0.2
            },
            surprised: {
                eyebrowY: 0.22,
                eyebrowRotation: 0,
                eyeScale: 1.3,
                mouthCurve: 0.5
            },
            speaking: {
                eyebrowY: 0.18,
                eyebrowRotation: 0,
                eyeScale: 1.05,
                mouthCurve: 0.1
            }
        };
        
        this.currentExpression = 'neutral';
        this.targetExpression = 'neutral';
        this.expressionBlend = 0;
    }
    
    setFacialExpression(expression, intensity = 1.0) {
        if (this.facialExpressions[expression]) {
            this.targetExpression = expression;
            this.expressionIntensity = intensity;
        }
    }
    
    updateFacialExpression(deltaTime) {
        if (!this.facialExpressions || this.targetExpression === this.currentExpression) return;
        
        // Blend between expressions
        this.expressionBlend = THREE.MathUtils.lerp(this.expressionBlend, 1.0, deltaTime * 5);
        
        const currentExpr = this.facialExpressions[this.currentExpression];
        const targetExpr = this.facialExpressions[this.targetExpression];
        const blend = this.expressionBlend;
        
        // Update eyebrows
        if (this.eyes) {
            this.eyes.children.forEach((child, index) => {
                if (child.type === 'Mesh' && child.position.y > 0.15) {
                    // This is an eyebrow
                    const targetY = THREE.MathUtils.lerp(
                        currentExpr.eyebrowY,
                        targetExpr.eyebrowY,
                        blend
                    );
                    const targetRot = THREE.MathUtils.lerp(
                        currentExpr.eyebrowRotation,
                        targetExpr.eyebrowRotation * (index === 0 ? -1 : 1),
                        blend
                    );
                    child.position.y = targetY;
                    child.rotation.z = targetRot;
                }
            });
        }
        
        // Update eye scale
        if (this.leftEye && this.rightEye) {
            const eyeScale = THREE.MathUtils.lerp(
                currentExpr.eyeScale,
                targetExpr.eyeScale,
                blend
            );
            this.leftEye.scale.y = eyeScale;
            this.rightEye.scale.y = eyeScale;
        }
        
        if (this.expressionBlend >= 0.99) {
            this.currentExpression = this.targetExpression;
            this.expressionBlend = 0;
        }
    }
    
    // Advanced body animation with IK (Inverse Kinematics) simulation
    createIKSystem() {
        // Store bone hierarchy for IK calculations
        this.boneHierarchy = {
            leftArm: {
                shoulder: { x: -0.7, y: 2.0, z: 0 },
                elbow: { x: -0.85, y: 1.35, z: 0 },
                wrist: { x: -1.05, y: 0.75, z: 0 }
            },
            rightArm: {
                shoulder: { x: 0.7, y: 2.0, z: 0 },
                elbow: { x: 0.85, y: 1.35, z: 0 },
                wrist: { x: 0.95, y: 0.75, z: 0 }
            }
        };
        
        // Target positions for IK
        this.ikTargets = {
            leftHand: { x: -1.2, y: 0.75, z: 0 },
            rightHand: { x: 0.95, y: 0.75, z: 0 }
        };
    }
    
    updateIKSystem(deltaTime, currentTime) {
        // Simple IK simulation for natural arm movement
        if (!this.leftArm || !this.rightArm) return;
        
        // Left arm IK (trident holding)
        const leftTarget = this.ikTargets.leftHand;
        const leftShoulder = this.boneHierarchy.leftArm.shoulder;
        
        // Calculate angles for natural arm position
        const dx = leftTarget.x - leftShoulder.x;
        const dy = leftTarget.y - leftShoulder.y;
        const dz = leftTarget.z - leftShoulder.z;
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
        
        // Update arm rotation based on target
        if (this.leftArm.children.length > 1) {
            const upperArm = this.leftArm.children[1];
            if (upperArm && upperArm.type === 'Mesh') {
                const targetAngle = Math.atan2(dy, Math.sqrt(dx * dx + dz * dz));
                upperArm.rotation.z = THREE.MathUtils.lerp(
                    upperArm.rotation.z,
                    targetAngle,
                    deltaTime * 2
                );
            }
        }
        
        // Right arm natural positioning
        const rightTarget = this.ikTargets.rightHand;
        const rightShoulder = this.boneHierarchy.rightArm.shoulder;
        
        const rdx = rightTarget.x - rightShoulder.x;
        const rdy = rightTarget.y - rightShoulder.y;
        
        if (this.rightArm && this.rightArm.children.length > 1) {
            const rightUpperArm = this.rightArm.children[1];
            if (rightUpperArm && rightUpperArm.type === 'Mesh') {
                const rightTargetAngle = Math.atan2(rdy, rdx) - Math.PI / 2;
                rightUpperArm.rotation.z = THREE.MathUtils.lerp(
                    rightUpperArm.rotation.z,
                    rightTargetAngle,
                    deltaTime * 2
                );
            }
        }
    }
    
    // Advanced water ripple system
    createWaterRippleSystem() {
        this.rippleGeometry = new THREE.RingGeometry(0.1, 2, 32);
        this.rippleMaterial = new THREE.MeshStandardMaterial({
            color: 0x00bfff,
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide,
            emissive: 0x00bfff,
            emissiveIntensity: 0.2
        });
        
        this.ripples = [];
        this.maxRipples = 10;
    }
    
    createRipple(x, y, z) {
        if (this.ripples.length >= this.maxRipples) {
            const oldRipple = this.ripples.shift();
            this.scene.remove(oldRipple);
            oldRipple.geometry.dispose();
            oldRipple.material.dispose();
        }
        
        const ripple = new THREE.Mesh(this.rippleGeometry, this.rippleMaterial.clone());
        ripple.position.set(x, y, z);
        ripple.rotation.x = -Math.PI / 2;
        ripple.scale.setScalar(0.1);
        ripple.userData = { age: 0, lifetime: 2.0 };
        
        this.scene.add(ripple);
        this.ripples.push(ripple);
    }
    
    updateWaterRipples(deltaTime) {
        this.ripples.forEach((ripple, index) => {
            ripple.userData.age += deltaTime;
            const progress = ripple.userData.age / ripple.userData.lifetime;
            
            if (progress >= 1.0) {
                this.scene.remove(ripple);
                ripple.geometry.dispose();
                ripple.material.dispose();
                this.ripples.splice(index, 1);
                return;
            }
            
            // Expand ripple
            const scale = 0.1 + progress * 2.0;
            ripple.scale.setScalar(scale);
            
            // Fade out
            if (ripple.material) {
                ripple.material.opacity = 0.3 * (1 - progress);
                ripple.material.emissiveIntensity = 0.2 * (1 - progress);
            }
        });
    }
    
    // Advanced particle trail system
    createParticleTrailSystem() {
        this.trailGeometry = new THREE.BufferGeometry();
        const trailCount = 50;
        const trailPositions = new Float32Array(trailCount * 3);
        const trailLifetimes = new Float32Array(trailCount);
        
        for (let i = 0; i < trailCount; i++) {
            const i3 = i * 3;
            trailPositions[i3] = 0;
            trailPositions[i3 + 1] = 0;
            trailPositions[i3 + 2] = 0;
            trailLifetimes[i] = 0;
        }
        
        this.trailGeometry.setAttribute('position', new THREE.BufferAttribute(trailPositions, 3));
        this.trailGeometry.setAttribute('lifetime', new THREE.BufferAttribute(trailLifetimes, 1));
        
        const trailMaterial = new THREE.PointsMaterial({
            color: 0x00ffff,
            size: 0.05,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });
        
        this.particleTrail = new THREE.Points(this.trailGeometry, trailMaterial);
        this.scene.add(this.particleTrail);
        this.trailIndex = 0;
        this.lastTrailPosition = new THREE.Vector3(0, 2, 0);
    }
    
    updateParticleTrail(deltaTime) {
        if (!this.particleTrail || !this.trident) return;
        
        // Get trident tip position
        const tridentTip = new THREE.Vector3();
        if (this.tridentProngs && this.tridentProngs.children.length > 0) {
            const centerProng = this.tridentProngs.children[0];
            centerProng.getWorldPosition(tridentTip);
        }
        
        // Check if moved enough to add new trail point
        const distance = this.lastTrailPosition.distanceTo(tridentTip);
        if (distance > 0.1) {
            const positions = this.particleTrail.geometry.attributes.position.array;
            const lifetimes = this.particleTrail.geometry.attributes.lifetime.array;
            
            const i3 = this.trailIndex * 3;
            positions[i3] = tridentTip.x;
            positions[i3 + 1] = tridentTip.y;
            positions[i3 + 2] = tridentTip.z;
            lifetimes[this.trailIndex] = 1.0;
            
            this.trailIndex = (this.trailIndex + 1) % 50;
            this.lastTrailPosition.copy(tridentTip);
            
            this.particleTrail.geometry.attributes.position.needsUpdate = true;
        }
        
        // Age trail particles
        const lifetimes = this.particleTrail.geometry.attributes.lifetime.array;
        for (let i = 0; i < lifetimes.length; i++) {
            if (lifetimes[i] > 0) {
                lifetimes[i] -= deltaTime * 0.5;
                if (lifetimes[i] < 0) lifetimes[i] = 0;
            }
        }
        this.particleTrail.geometry.attributes.lifetime.needsUpdate = true;
    }
    
    // Advanced depth of field simulation using fog
    updateDepthOfField(currentTime) {
        if (this.scene.fog) {
            // Adjust fog based on focus
            const focusDistance = 8;
            const focusRange = 3;
            
            this.scene.fog.near = focusDistance - focusRange;
            this.scene.fog.far = focusDistance + focusRange;
        }
    }
    
    // Advanced shadow system
    enhanceShadowSystem() {
        // Add more shadow-casting lights
        if (this.mainLight) {
            // Increase shadow quality
            this.mainLight.shadow.mapSize.width = 4096;
            this.mainLight.shadow.mapSize.height = 4096;
            this.mainLight.shadow.radius = 8;
            this.mainLight.shadow.bias = -0.0001;
        }
        
        // Add soft shadow helper
        this.scene.traverse((object) => {
            if (object.castShadow !== undefined) {
                object.castShadow = true;
            }
            if (object.receiveShadow !== undefined && object.position.y < 0) {
                object.receiveShadow = true;
            }
        });
    }
    
    // Advanced texture detail system
    createTextureDetails() {
        // Add procedural texture details using geometry
        // Skin pores
        const poreGeometry = new THREE.SphereGeometry(0.002, 6, 6);
        const poreMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.skinDark,
            roughness: 0.9
        });
        
        // Add pores to face
        if (this.headMesh) {
            for (let i = 0; i < 200; i++) {
                const pore = new THREE.Mesh(poreGeometry, poreMaterial);
                const angle1 = Math.random() * Math.PI * 2;
                const angle2 = Math.random() * Math.PI;
                const radius = 0.38 + (Math.random() - 0.5) * 0.05;
                pore.position.set(
                    Math.sin(angle2) * Math.cos(angle1) * radius,
                    Math.cos(angle2) * radius,
                    Math.sin(angle2) * Math.sin(angle1) * radius + 0.35
                );
                this.headMesh.add(pore);
            }
        }
        
        // Add skin texture to body
        if (this.body) {
            for (let i = 0; i < 300; i++) {
                const pore = new THREE.Mesh(poreGeometry, poreMaterial);
                const angle = Math.random() * Math.PI * 2;
                const height = Math.random() * 1.8 - 0.9;
                const radius = 0.6 + Math.random() * 0.2;
                pore.position.set(
                    Math.cos(angle) * radius,
                    height,
                    Math.sin(angle) * radius * 0.8
                );
                this.body.add(pore);
            }
        }
    }
    
    // Advanced animation blending system
    createAnimationBlending() {
        this.animationLayers = {
            base: { weight: 1.0, animations: [] },
            breathing: { weight: 1.0, animations: [] },
            speaking: { weight: 0.0, animations: [] },
            gestures: { weight: 0.5, animations: [] }
        };
    }
    
    blendAnimations(deltaTime) {
        // Smoothly blend between animation layers
        Object.keys(this.animationLayers).forEach(layerName => {
            const layer = this.animationLayers[layerName];
            // Animation blending logic would go here
            // For now, just update weights smoothly
        });
    }
    
    // Enhanced update method that calls all systems
    updateAdvancedAnimations(deltaTime, currentTime) {
        // Call original update
        // (This would be the previous updateAdvancedAnimations code)
        
        // Update new systems
        this.updateFacialExpression(deltaTime);
        this.updateIKSystem(deltaTime, currentTime);
        this.updateWaterRipples(deltaTime);
        this.updateParticleTrail(deltaTime);
        this.updateDepthOfField(currentTime);
        this.blendAnimations(deltaTime);
        
        // Set facial expression based on state
        if (this.isSpeaking) {
            this.setFacialExpression('speaking', 0.8);
        } else {
            this.setFacialExpression('neutral', 1.0);
        }
    }
    
    // Performance optimization system
    optimizePerformance() {
        // Level of Detail (LOD) system
        this.lodLevels = {
            high: { distance: 5, enabled: true },
            medium: { distance: 15, enabled: true },
            low: { distance: 25, enabled: true }
        };
        
        // Frustum culling is automatic in Three.js
        // But we can optimize geometry complexity based on distance
        this.updateLOD();
    }
    
    updateLOD() {
        if (!this.camera || !this.poseidon) return;
        
        const distance = this.camera.position.distanceTo(this.poseidon.position);
        
        // Adjust geometry complexity based on distance
        // This is a simplified version - full LOD would use different geometries
        this.scene.traverse((object) => {
            if (object.geometry && object.geometry.type === 'BufferGeometry') {
                // Could reduce vertex count based on distance
                // For now, just ensure proper culling
            }
        });
    }
    
    // Enhanced initialization that includes all new systems
    enhanceInitialization() {
        // Call existing enhancements
        this.enhanceLightingSystem();
        this.createAdvancedEnvironment();
        this.createWaterSurface();
        this.createMuscleDetailSystem();
        this.createHairPhysics();
        this.addCharacterDetails();
        this.addTridentDetails();
        this.createAdvancedParticles();
        this.setupPostProcessing();
        
        // Add new systems
        this.createFacialExpressionSystem();
        this.createIKSystem();
        this.createWaterRippleSystem();
        this.createParticleTrailSystem();
        this.enhanceShadowSystem();
        this.createTextureDetails();
        this.createAnimationBlending();
        this.optimizePerformance();
        
        console.log('[Poseidon3D] All advanced features initialized');
    }
    
    // Additional advanced rendering features
    
    // Screen-space ambient occlusion simulation
    createSSAO() {
        // Simulate SSAO using darker materials in crevices
        this.scene.traverse((object) => {
            if (object.material && object.geometry) {
                // Add darker material variant for occlusion simulation
                const originalColor = object.material.color;
                if (originalColor) {
                    object.material.aoMapIntensity = 0.5;
                }
            }
        });
    }
    
    // Advanced reflection system
    createReflectionSystem() {
        // Create reflection planes for water surface
        const reflectionGeometry = new THREE.PlaneGeometry(20, 20, 32, 32);
        const reflectionMaterial = new THREE.MeshStandardMaterial({
            color: 0x0088ff,
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide,
            roughness: 0.1,
            metalness: 0.9
        });
        
        const reflection = new THREE.Mesh(reflectionGeometry, reflectionMaterial);
        reflection.rotation.x = Math.PI / 2;
        reflection.position.y = -0.5;
        this.scene.add(reflection);
        this.reflectionPlane = reflection;
    }
    
    updateReflectionSystem(currentTime) {
        if (this.reflectionPlane && this.waterSurface) {
            // Mirror water surface for reflection
            const waterPositions = this.waterSurface.geometry.attributes.position;
            const reflectionPositions = this.reflectionPlane.geometry.attributes.position;
            
            for (let i = 0; i < waterPositions.count; i++) {
                const z = waterPositions.getZ(i);
                reflectionPositions.setZ(i, -z);
            }
            
            this.reflectionPlane.geometry.computeVertexNormals();
            this.reflectionPlane.geometry.attributes.position.needsUpdate = true;
        }
    }
    
    // Advanced color grading system
    createColorGrading() {
        // Color grading is typically done in post-processing
        // For now, adjust scene colors for blue theme consistency
        this.scene.traverse((object) => {
            if (object.material) {
                // Ensure all materials have blue tint
                if (object.material.color && !object.material.emissive) {
                    // Slight blue tint to non-emissive materials
                    const color = object.material.color;
                    if (color.r > color.b) {
                        // Shift towards blue
                        color.r *= 0.95;
                        color.g *= 0.98;
                        color.b *= 1.05;
                    }
                }
            }
        });
    }
    
    // Advanced muscle flex animation
    createMuscleFlexSystem() {
        this.muscleFlexData = {
            biceps: { flex: 0, targetFlex: 0 },
            triceps: { flex: 0, targetFlex: 0 },
            chest: { flex: 0, targetFlex: 0 },
            abs: { flex: 0, targetFlex: 0 }
        };
    }
    
    updateMuscleFlex(deltaTime) {
        if (!this.muscleFlexData) return;
        
        // Flex muscles when speaking or gesturing
        if (this.isSpeaking) {
            this.muscleFlexData.biceps.targetFlex = 0.1;
            this.muscleFlexData.chest.targetFlex = 0.15;
        } else {
            this.muscleFlexData.biceps.targetFlex = 0;
            this.muscleFlexData.chest.targetFlex = 0;
        }
        
        // Smoothly interpolate muscle flex
        Object.keys(this.muscleFlexData).forEach(muscle => {
            const data = this.muscleFlexData[muscle];
            data.flex = THREE.MathUtils.lerp(data.flex, data.targetFlex, deltaTime * 5);
        });
        
        // Apply flex to body parts
        if (this.body) {
            this.body.scale.x = 1.0 + this.muscleFlexData.chest.flex * 0.1;
            this.body.scale.z = 1.0 + this.muscleFlexData.chest.flex * 0.15;
        }
    }
    
    // Advanced hand gesture system
    createGestureSystem() {
        this.gestureStates = {
            idle: { fingerSpread: 0, fingerCurl: 0 },
            pointing: { fingerSpread: 0.3, fingerCurl: 0.7 },
            open: { fingerSpread: 0.8, fingerCurl: 0.1 },
            fist: { fingerSpread: 0, fingerCurl: 1.0 }
        };
        
        this.currentGesture = 'idle';
        this.targetGesture = 'idle';
    }
    
    setGesture(hand, gesture) {
        if (this.gestureStates[gesture]) {
            this.targetGesture = gesture;
        }
    }
    
    updateGestures(deltaTime) {
        // Animate hand gestures
        if (this.leftHand && this.targetGesture !== this.currentGesture) {
            const targetState = this.gestureStates[this.targetGesture];
            const currentState = this.gestureStates[this.currentGesture];
            
            // Animate fingers towards target gesture
            this.leftHand.children.forEach((finger, index) => {
                if (index > 0 && finger.type === 'Mesh') {
                    const targetCurl = THREE.MathUtils.lerp(
                        currentState.fingerCurl,
                        targetState.fingerCurl,
                        deltaTime * 5
                    );
                    finger.rotation.x = -targetCurl * Math.PI / 3;
                }
            });
            
            if (Math.abs(targetState.fingerCurl - currentState.fingerCurl) < 0.01) {
                this.currentGesture = this.targetGesture;
            }
        }
    }
    
    // Advanced breathing system with chest expansion
    enhanceBreathingSystem() {
        this.breathingPhases = {
            inhale: { duration: 2.0, chestScale: 1.05, shoulderLift: 0.02 },
            hold: { duration: 0.5, chestScale: 1.05, shoulderLift: 0.02 },
            exhale: { duration: 2.5, chestScale: 0.98, shoulderLift: -0.01 },
            rest: { duration: 1.0, chestScale: 1.0, shoulderLift: 0 }
        };
        
        this.currentBreathingPhase = 'inhale';
        this.breathingPhaseTime = 0;
    }
    
    updateBreathingSystem(deltaTime) {
        if (!this.breathingPhases) return;
        
        this.breathingPhaseTime += deltaTime;
        const currentPhase = this.breathingPhases[this.currentBreathingPhase];
        
        if (this.breathingPhaseTime >= currentPhase.duration) {
            // Move to next phase
            const phaseOrder = ['inhale', 'hold', 'exhale', 'rest'];
            const currentIndex = phaseOrder.indexOf(this.currentBreathingPhase);
            this.currentBreathingPhase = phaseOrder[(currentIndex + 1) % phaseOrder.length];
            this.breathingPhaseTime = 0;
        }
        
        const phase = this.breathingPhases[this.currentBreathingPhase];
        const progress = this.breathingPhaseTime / phase.duration;
        
        // Apply breathing to body
        if (this.body) {
            const chestScale = THREE.MathUtils.smoothstep(0, 1, progress) * 
                             (phase.chestScale - 1.0) + 1.0;
            this.body.scale.y = chestScale;
            this.body.scale.x = chestScale * 0.9;
        }
        
        // Lift shoulders slightly
        if (this.arms) {
            this.arms.position.y = phase.shoulderLift * Math.sin(progress * Math.PI);
        }
    }
    
    // Advanced eye tracking system
    createEyeTrackingSystem() {
        this.eyeTarget = new THREE.Vector3(0, 1.5, 5);
        this.eyeTrackingSpeed = 2.0;
    }
    
    setEyeTarget(target) {
        if (target instanceof THREE.Vector3) {
            this.eyeTarget.copy(target);
        } else if (Array.isArray(target) && target.length >= 3) {
            this.eyeTarget.set(target[0], target[1], target[2]);
        }
    }
    
    updateEyeTracking(deltaTime) {
        if (!this.leftEye || !this.rightEye || !this.leftPupil || !this.rightPupil) return;
        
        // Calculate eye direction
        const leftEyeWorld = new THREE.Vector3();
        const rightEyeWorld = new THREE.Vector3();
        this.leftEye.getWorldPosition(leftEyeWorld);
        this.rightEye.getWorldPosition(rightEyeWorld);
        
        const leftDirection = new THREE.Vector3()
            .subVectors(this.eyeTarget, leftEyeWorld)
            .normalize();
        const rightDirection = new THREE.Vector3()
            .subVectors(this.eyeTarget, rightEyeWorld)
            .normalize();
        
        // Convert to local eye space and move pupils
        const leftLocal = new THREE.Vector3()
            .copy(leftDirection)
            .applyQuaternion(this.leftEye.quaternion.clone().invert());
        const rightLocal = new THREE.Vector3()
            .copy(rightDirection)
            .applyQuaternion(this.rightEye.quaternion.clone().invert());
        
        // Limit pupil movement
        const maxOffset = 0.02;
        this.leftPupil.position.x = THREE.MathUtils.clamp(leftLocal.x * 0.1, -maxOffset, maxOffset);
        this.leftPupil.position.y = THREE.MathUtils.clamp(leftLocal.y * 0.1, -maxOffset, maxOffset);
        this.rightPupil.position.x = THREE.MathUtils.clamp(rightLocal.x * 0.1, -maxOffset, maxOffset);
        this.rightPupil.position.y = THREE.MathUtils.clamp(rightLocal.y * 0.1, -maxOffset, maxOffset);
    }
    
    // Enhanced initialization that includes ALL systems
    enhanceInitialization() {
        // Lighting and environment
        this.enhanceLightingSystem();
        this.createAdvancedEnvironment();
        this.createWaterSurface();
        this.createReflectionSystem();
        
        // Character details
        this.createMuscleDetailSystem();
        this.createHairPhysics();
        this.addCharacterDetails();
        this.createTextureDetails();
        
        // Trident enhancements
        this.addTridentDetails();
        
        // Particle systems
        this.createAdvancedParticles();
        this.createWaterRippleSystem();
        this.createParticleTrailSystem();
        
        // Animation systems
        this.createFacialExpressionSystem();
        this.createIKSystem();
        this.createAnimationBlending();
        this.createMuscleFlexSystem();
        this.createGestureSystem();
        this.enhanceBreathingSystem();
        this.createEyeTrackingSystem();
        
        // Rendering enhancements
        this.setupPostProcessing();
        this.enhanceShadowSystem();
        this.createSSAO();
        this.createColorGrading();
        this.optimizePerformance();
        this.enhanceCullingSystem();
        this.createMaterialVariations();
        this.createDeformationSystem();
        this.createAudioReactiveSystem();
        this.createProceduralDetails();
        this.createMotionBlurSystem();
        
        console.log('[Poseidon3D] All advanced features initialized');
    }
    
    // Utility methods and helper functions
    
    // Color utility functions
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16) / 255,
            g: parseInt(result[2], 16) / 255,
            b: parseInt(result[3], 16) / 255
        } : null;
    }
    
    rgbToHex(r, g, b) {
        return "#" + ((1 << 24) + (Math.round(r * 255) << 16) + (Math.round(g * 255) << 8) + Math.round(b * 255)).toString(16).slice(1);
    }
    
    // Geometry utility functions
    createSmoothGeometry(baseGeometry, smoothingIterations = 1) {
        // Simple smoothing algorithm
        const positions = baseGeometry.attributes.position.array;
        const newPositions = new Float32Array(positions);
        
        for (let iter = 0; iter < smoothingIterations; iter++) {
            for (let i = 3; i < positions.length - 3; i += 3) {
                newPositions[i] = (positions[i - 3] + positions[i] + positions[i + 3]) / 3;
                newPositions[i + 1] = (positions[i - 2] + positions[i + 1] + positions[i + 4]) / 3;
                newPositions[i + 2] = (positions[i - 1] + positions[i + 2] + positions[i + 5]) / 3;
            }
            positions.set(newPositions);
        }
        
        baseGeometry.computeVertexNormals();
        return baseGeometry;
    }
    
    // Animation easing functions
    easeInOutQuad(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }
    
    easeInCubic(t) {
        return t * t * t;
    }
    
    easeOutCubic(t) {
        return (--t) * t * t + 1;
    }
    
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    }
    
    // Vector utility functions
    lerpVector3(v1, v2, t) {
        return new THREE.Vector3().lerpVectors(v1, v2, t);
    }
    
    // Distance utility
    distance3D(pos1, pos2) {
        const dx = pos2.x - pos1.x;
        const dy = pos2.y - pos1.y;
        const dz = pos2.z - pos1.z;
        return Math.sqrt(dx * dx + dy * dy + dz * dz);
    }
    
    // Angle utility
    angleBetweenVectors(v1, v2) {
        return Math.acos(v1.dot(v2) / (v1.length() * v2.length()));
    }
    
    // Noise function for procedural generation
    noise3D(x, y, z) {
        // Simple 3D noise implementation
        const p = new Array(512);
        const permutation = [151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180];
        
        for (let i = 0; i < 256; i++) {
            p[256 + i] = p[i] = permutation[i];
        }
        
        const X = Math.floor(x) & 255;
        const Y = Math.floor(y) & 255;
        const Z = Math.floor(z) & 255;
        
        x -= Math.floor(x);
        y -= Math.floor(y);
        z -= Math.floor(z);
        
        const u = this.fade(x);
        const v = this.fade(y);
        const w = this.fade(z);
        
        const A = p[X] + Y;
        const AA = p[A] + Z;
        const AB = p[A + 1] + Z;
        const B = p[X + 1] + Y;
        const BA = p[B] + Z;
        const BB = p[B + 1] + Z;
        
        return this.lerp(w,
            this.lerp(v,
                this.lerp(u, this.grad(p[AA], x, y, z),
                    this.grad(p[BA], x - 1, y, z)),
                this.lerp(u, this.grad(p[AB], x, y - 1, z),
                    this.grad(p[BB], x - 1, y - 1, z))),
            this.lerp(v,
                this.lerp(u, this.grad(p[AA + 1], x, y, z - 1),
                    this.grad(p[BA + 1], x - 1, y, z - 1)),
                this.lerp(u, this.grad(p[AB + 1], x, y - 1, z - 1),
                    this.grad(p[BB + 1], x - 1, y - 1, z - 1))));
    }
    
    fade(t) {
        return t * t * t * (t * (t * 6 - 15) + 10);
    }
    
    lerp(t, a, b) {
        return a + t * (b - a);
    }
    
    grad(hash, x, y, z) {
        const h = hash & 15;
        const u = h < 8 ? x : y;
        const v = h < 4 ? y : h === 12 || h === 14 ? x : z;
        return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
    }
    
    // Performance monitoring
    startPerformanceMonitoring() {
        this.performanceStats = {
            frameCount: 0,
            lastFpsUpdate: performance.now(),
            fps: 60,
            frameTime: 0,
            averageFrameTime: 0,
            minFrameTime: Infinity,
            maxFrameTime: 0
        };
    }
    
    updatePerformanceMonitoring(deltaTime) {
        if (!this.performanceStats) return;
        
        this.performanceStats.frameCount++;
        this.performanceStats.frameTime = deltaTime * 1000;
        
        const frameTime = this.performanceStats.frameTime;
        this.performanceStats.averageFrameTime = 
            (this.performanceStats.averageFrameTime * (this.performanceStats.frameCount - 1) + frameTime) / 
            this.performanceStats.frameCount;
        
        if (frameTime < this.performanceStats.minFrameTime) {
            this.performanceStats.minFrameTime = frameTime;
        }
        if (frameTime > this.performanceStats.maxFrameTime) {
            this.performanceStats.maxFrameTime = frameTime;
        }
        
        // Update FPS every second
        const now = performance.now();
        if (now - this.performanceStats.lastFpsUpdate >= 1000) {
            this.performanceStats.fps = this.performanceStats.frameCount;
            this.performanceStats.frameCount = 0;
            this.performanceStats.lastFpsUpdate = now;
            
            // Log performance if needed
            if (this.performanceStats.fps < 30) {
                console.warn('[Poseidon3D] Low FPS:', this.performanceStats.fps);
            }
        }
    }
    
    getPerformanceStats() {
        return this.performanceStats || null;
    }
    
    // Debug visualization helpers
    createDebugHelpers() {
        // Create axes helper
        const axesHelper = new THREE.AxesHelper(5);
        this.scene.add(axesHelper);
        this.axesHelper = axesHelper;
        
        // Create grid helper
        const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
        gridHelper.position.y = -0.5;
        this.scene.add(gridHelper);
        this.gridHelper = gridHelper;
        
        // Create light helpers (optional, for debugging)
        if (this.mainLight) {
            const lightHelper = new THREE.DirectionalLightHelper(this.mainLight, 1);
            this.scene.add(lightHelper);
            this.lightHelper = lightHelper;
        }
    }
    
    toggleDebugHelpers() {
        if (this.axesHelper) this.axesHelper.visible = !this.axesHelper.visible;
        if (this.gridHelper) this.gridHelper.visible = !this.gridHelper.visible;
        if (this.lightHelper) this.lightHelper.visible = !this.lightHelper.visible;
    }
    
    // Camera controls utility
    setCameraPosition(x, y, z) {
        if (this.camera) {
            this.camera.position.set(x, y, z);
            this.camera.lookAt(0, 1.5, 0);
        }
    }
    
    setCameraTarget(x, y, z) {
        if (this.camera) {
            this.camera.lookAt(x, y, z);
        }
    }
    
    // Animation state management
    getAnimationState() {
        return {
            isSpeaking: this.isSpeaking,
            speechTime: this.speechTime,
            mouthOpenness: this.mouthOpenness,
            currentExpression: this.currentExpression,
            breathingPhase: this.currentBreathingPhase,
            frameCount: this.frameCount
        };
    }
    
    // Reset animation state
    resetAnimationState() {
        this.isSpeaking = false;
        this.speechTime = 0;
        this.mouthOpenness = 0;
        this.currentExpression = 'neutral';
        this.targetExpression = 'neutral';
        this.expressionBlend = 0;
        
        if (this.mouthOpening) {
            this.mouthOpening.scale.set(1, 0, 1);
        }
    }
    
    // Quality settings
    setQualityLevel(level) {
        // level: 'low', 'medium', 'high', 'ultra'
        this.qualityLevel = level;
        
        switch (level) {
            case 'low':
                this.renderer.setPixelRatio(1);
                if (this.waterParticles) this.waterParticles.visible = false;
                if (this.sparkleParticles) this.sparkleParticles.visible = false;
                break;
            case 'medium':
                this.renderer.setPixelRatio(1.5);
                if (this.waterParticles) this.waterParticles.visible = true;
                if (this.sparkleParticles) this.sparkleParticles.visible = false;
                break;
            case 'high':
                this.renderer.setPixelRatio(2);
                if (this.waterParticles) this.waterParticles.visible = true;
                if (this.sparkleParticles) this.sparkleParticles.visible = true;
                break;
            case 'ultra':
                this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 3));
                if (this.waterParticles) this.waterParticles.visible = true;
                if (this.sparkleParticles) this.sparkleParticles.visible = true;
                break;
        }
    }
    
    // Export scene data (for debugging/saving)
    exportSceneData() {
        const sceneData = {
            camera: {
                position: this.camera ? {
                    x: this.camera.position.x,
                    y: this.camera.position.y,
                    z: this.camera.position.z
                } : null,
                rotation: this.camera ? {
                    x: this.camera.rotation.x,
                    y: this.camera.rotation.y,
                    z: this.camera.rotation.z
                } : null
            },
            lights: [],
            objects: []
        };
        
        this.scene.traverse((object) => {
            if (object.type === 'Light') {
                sceneData.lights.push({
                    type: object.type,
                    color: object.color ? object.color.getHex() : 0xffffff,
                    intensity: object.intensity,
                    position: {
                        x: object.position.x,
                        y: object.position.y,
                        z: object.position.z
                    }
                });
            } else if (object.type === 'Mesh') {
                sceneData.objects.push({
                    type: object.type,
                    name: object.name || 'unnamed',
                    position: {
                        x: object.position.x,
                        y: object.position.y,
                        z: object.position.z
                    }
                });
            }
        });
        
        return sceneData;
    }
    
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Poseidon3D;
}


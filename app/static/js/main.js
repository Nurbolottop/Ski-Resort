/* =============================================================================
   Тоо-Ашуу — интерактив сайта. Без зависимостей.
   Всё работает как прогрессивное улучшение: без JS сайт остаётся рабочим.
   ============================================================================= */
(function () {
    'use strict';

    var root = document.documentElement;
    root.classList.remove('no-js');
    root.classList.add('js');

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function $(selector, scope) { return (scope || document).querySelector(selector); }
    function $$(selector, scope) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }

    /* ---------------------------------------------------------------------
       Шапка: фон при прокрутке
       --------------------------------------------------------------------- */
    function initHeader() {
        var header = $('.header');
        if (!header) return;
        var solid = document.body.classList.contains('page-inner');
        function update() {
            header.classList.toggle('is-scrolled', solid || window.scrollY > 40);
        }
        update();
        window.addEventListener('scroll', update, { passive: true });
    }

    /* ---------------------------------------------------------------------
       Мобильное меню
       --------------------------------------------------------------------- */
    function initNav() {
        var burger = $('[data-burger]');
        if (!burger) return;
        function setOpen(open) {
            document.body.classList.toggle('nav-open', open);
            if (window.__lenis) { if (open) window.__lenis.stop(); else window.__lenis.start(); }
            burger.setAttribute('aria-expanded', open ? 'true' : 'false');
        }
        burger.addEventListener('click', function () {
            setOpen(!document.body.classList.contains('nav-open'));
        });
        $$('.nav a').forEach(function (link) {
            link.addEventListener('click', function () { setOpen(false); });
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') setOpen(false);
        });
        window.addEventListener('resize', function () {
            if (window.innerWidth > 1180) setOpen(false);
        });
    }

    /* ---------------------------------------------------------------------
       Слайдер на главной
       --------------------------------------------------------------------- */
    function initSlider() {
        var hero = $('[data-slider]');
        if (!hero) return;
        var slides = $$('[data-slide]', hero);
        var dots = $$('[data-slide-to]', hero);
        if (slides.length < 2) {
            if (slides[0]) slides[0].classList.add('is-active');
            return;
        }

        var duration = 7000;
        var current = 0;
        var timer = null;
        hero.style.setProperty('--slide-duration', duration + 'ms');

        function go(index) {
            slides[current].classList.remove('is-active');
            if (dots[current]) dots[current].classList.remove('is-active');
            current = (index + slides.length) % slides.length;
            slides[current].classList.add('is-active');
            if (dots[current]) {
                // Перезапуск анимации прогресса
                dots[current].classList.remove('is-active');
                void dots[current].offsetWidth;
                dots[current].classList.add('is-active');
            }
        }

        function start() {
            if (reduceMotion) return;
            stop();
            timer = setInterval(function () { go(current + 1); }, duration);
        }

        function stop() {
            if (timer) clearInterval(timer);
            timer = null;
        }

        dots.forEach(function (dot) {
            dot.addEventListener('click', function () {
                go(parseInt(dot.getAttribute('data-slide-to'), 10));
                start();
            });
        });

        var prev = $('[data-slider-prev]', hero);
        var next = $('[data-slider-next]', hero);
        if (prev) prev.addEventListener('click', function () { go(current - 1); start(); });
        if (next) next.addEventListener('click', function () { go(current + 1); start(); });

        // Пауза при наведении на текст/контролы
        var pauseZone = $('.hero__controls', hero);
        [pauseZone].forEach(function (zone) {
            if (!zone) return;
            zone.addEventListener('mouseenter', function () { stop(); hero.classList.add('is-paused'); });
            zone.addEventListener('mouseleave', function () { start(); hero.classList.remove('is-paused'); });
        });

        // Свайпы
        var startX = null;
        hero.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
        hero.addEventListener('touchend', function (e) {
            if (startX === null) return;
            var dx = e.changedTouches[0].clientX - startX;
            if (Math.abs(dx) > 50) { go(current + (dx < 0 ? 1 : -1)); start(); }
            startX = null;
        });

        document.addEventListener('visibilitychange', function () {
            if (document.hidden) stop(); else start();
        });

        start();
    }

    /* ---------------------------------------------------------------------
       Появление блоков и счётчики
       --------------------------------------------------------------------- */
    function animateCount(el) {
        var target = parseFloat(el.getAttribute('data-count'));
        if (isNaN(target)) return;
        var decimals = (el.getAttribute('data-count').split('.')[1] || '').length;
        var startTime = null;
        var dur = 1600;
        function step(ts) {
            if (!startTime) startTime = ts;
            var p = Math.min((ts - startTime) / dur, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = (target * eased).toFixed(decimals).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
            if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    function initReveal() {
        var items = $$('[data-reveal]');
        var counters = $$('[data-count]');
        if (!('IntersectionObserver' in window) || reduceMotion) {
            items.forEach(function (el) { el.classList.add('is-visible'); });
            return;
        }
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('is-visible');
                io.unobserve(entry.target);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
        items.forEach(function (el) { io.observe(el); });

        var cio = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                animateCount(entry.target);
                cio.unobserve(entry.target);
            });
        }, { threshold: 0.6 });
        counters.forEach(function (el) { cio.observe(el); });
    }

    /* ---------------------------------------------------------------------
       Лайтбокс: <a data-lightbox="группа" href="фото" data-caption="...">
       --------------------------------------------------------------------- */
    function initLightbox() {
        var links = $$('[data-lightbox]');
        if (!links.length) return;

        var box = document.createElement('div');
        box.className = 'lightbox';
        box.setAttribute('role', 'dialog');
        box.setAttribute('aria-modal', 'true');
        box.innerHTML =
            '<figure class="lightbox__figure"><img class="lightbox__image" alt=""><figcaption class="lightbox__caption"></figcaption></figure>' +
            '<button class="lightbox__btn lightbox__close" type="button" aria-label="Закрыть"><svg class="icon"><use href="#i-close"></use></svg></button>' +
            '<button class="lightbox__btn lightbox__prev" type="button" aria-label="Предыдущее фото"><svg class="icon"><use href="#i-arrow-left"></use></svg></button>' +
            '<button class="lightbox__btn lightbox__next" type="button" aria-label="Следующее фото"><svg class="icon"><use href="#i-arrow-right"></use></svg></button>' +
            '<span class="lightbox__counter"></span>';
        document.body.appendChild(box);

        var img = $('.lightbox__image', box);
        var caption = $('.lightbox__caption', box);
        var counter = $('.lightbox__counter', box);
        var group = [];
        var index = 0;

        function visible(link) { return !link.closest('.is-hidden'); }

        function show(i) {
            index = (i + group.length) % group.length;
            var link = group[index];
            img.src = link.getAttribute('href');
            img.alt = link.getAttribute('data-caption') || '';
            caption.textContent = link.getAttribute('data-caption') || '';
            counter.textContent = (index + 1) + ' / ' + group.length;
            var multiple = group.length > 1;
            $('.lightbox__prev', box).hidden = !multiple;
            $('.lightbox__next', box).hidden = !multiple;
        }

        function open(link) {
            var name = link.getAttribute('data-lightbox');
            group = links.filter(function (l) { return l.getAttribute('data-lightbox') === name && visible(l); });
            show(group.indexOf(link));
            box.classList.add('is-open');
            document.body.classList.add('lightbox-open');
            if (window.__lenis) window.__lenis.stop();
        }

        function close() {
            box.classList.remove('is-open');
            document.body.classList.remove('lightbox-open');
            if (window.__lenis) window.__lenis.start();
        }

        links.forEach(function (link) {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                open(link);
            });
        });

        $('.lightbox__close', box).addEventListener('click', close);
        $('.lightbox__prev', box).addEventListener('click', function () { show(index - 1); });
        $('.lightbox__next', box).addEventListener('click', function () { show(index + 1); });
        box.addEventListener('click', function (e) { if (e.target === box) close(); });
        document.addEventListener('keydown', function (e) {
            if (!box.classList.contains('is-open')) return;
            if (e.key === 'Escape') close();
            if (e.key === 'ArrowLeft') show(index - 1);
            if (e.key === 'ArrowRight') show(index + 1);
        });

        var startX = null;
        box.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
        box.addEventListener('touchend', function (e) {
            if (startX === null) return;
            var dx = e.changedTouches[0].clientX - startX;
            if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
            startX = null;
        });
    }

    /* ---------------------------------------------------------------------
       Фильтр галереи по альбомам
       --------------------------------------------------------------------- */
    function initFilters() {
        $$('[data-filter-group]').forEach(function (bar) {
            var target = $(bar.getAttribute('data-filter-group'));
            if (!target) return;
            var buttons = $$('[data-filter]', bar);
            buttons.forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var value = btn.getAttribute('data-filter');
                    buttons.forEach(function (b) { b.classList.toggle('is-active', b === btn); });
                    $$('[data-album]', target).forEach(function (item) {
                        item.classList.toggle('is-hidden', value !== 'all' && item.getAttribute('data-album') !== value);
                    });
                });
            });
        });
    }

    /* ---------------------------------------------------------------------
       Активная вкладка при прокрутке (меню ресторана)
       --------------------------------------------------------------------- */
    function initScrollSpy() {
        var bar = $('[data-scrollspy]');
        if (!bar || !('IntersectionObserver' in window)) return;
        var links = $$('a[href^="#"]', bar);
        var map = {};
        links.forEach(function (link) {
            var section = $(link.getAttribute('href'));
            if (section) map[section.id] = link;
        });
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                links.forEach(function (l) { l.classList.remove('is-active'); });
                if (map[entry.target.id]) map[entry.target.id].classList.add('is-active');
            });
        }, { rootMargin: '-45% 0px -50% 0px' });
        Object.keys(map).forEach(function (id) { io.observe(document.getElementById(id)); });
    }

    /* ---------------------------------------------------------------------
       Формы: даты бронирования и защита от двойной отправки
       --------------------------------------------------------------------- */
    function iso(date) {
        var tz = date.getTimezoneOffset() * 60000;
        return new Date(date - tz).toISOString().slice(0, 10);
    }

    function initForms() {
        $$('form').forEach(function (form) {
            var checkIn = $('[name="check_in"]', form);
            var checkOut = $('[name="check_out"]', form);
            if (checkIn && checkOut) {
                var today = new Date();
                checkIn.min = iso(today);
                function sync() {
                    if (!checkIn.value) return;
                    var next = new Date(checkIn.value);
                    next.setDate(next.getDate() + 1);
                    checkOut.min = iso(next);
                    if (!checkOut.value || checkOut.value <= checkIn.value) checkOut.value = iso(next);
                }
                checkIn.addEventListener('change', sync);
                sync();
            }
            form.addEventListener('submit', function () {
                var btn = $('[type="submit"]', form);
                if (btn) btn.classList.add('is-loading');
            });
        });
    }

    /* ---------------------------------------------------------------------
       Всплывающие сообщения
       --------------------------------------------------------------------- */
    function initMessages() {
        $$('.message').forEach(function (msg, i) {
            function hide() {
                msg.classList.add('is-hiding');
                setTimeout(function () { msg.remove(); }, 400);
            }
            var btn = $('.message__close', msg);
            if (btn) btn.addEventListener('click', hide);
            setTimeout(hide, 7000 + i * 800);
        });
    }

    /* ---------------------------------------------------------------------
       Погода: Open-Meteo (бесплатно, без ключа)
       --------------------------------------------------------------------- */
    var WEATHER = {
        0: ['Ясно', 'sun'], 1: ['Преимущественно ясно', 'sun'], 2: ['Переменная облачность', 'cloud-sun'],
        3: ['Пасмурно', 'cloud'], 45: ['Туман', 'fog'], 48: ['Изморозь', 'fog'],
        51: ['Морось', 'rain'], 53: ['Морось', 'rain'], 55: ['Морось', 'rain'],
        61: ['Дождь', 'rain'], 63: ['Дождь', 'rain'], 65: ['Сильный дождь', 'rain'],
        66: ['Ледяной дождь', 'rain'], 67: ['Ледяной дождь', 'rain'],
        71: ['Небольшой снег', 'snow'], 73: ['Снег', 'snow'], 75: ['Сильный снег', 'snow'], 77: ['Снежная крупа', 'snow'],
        80: ['Ливень', 'rain'], 81: ['Ливень', 'rain'], 82: ['Сильный ливень', 'rain'],
        85: ['Снегопад', 'snow'], 86: ['Сильный снегопад', 'snow'],
        95: ['Гроза', 'storm'], 96: ['Гроза', 'storm'], 99: ['Гроза', 'storm']
    };

    var ICONS = {
        'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
        'cloud-sun': '<path d="M12 2v2M4.9 4.9l1.4 1.4M2 12h2M19.1 4.9l-1.4 1.4"/><path d="M15.9 11A4 4 0 0 0 8 12"/><path d="M17.5 21H9a5 5 0 1 1 4.6-7h1.4a3.5 3.5 0 1 1 2.5 7Z"/>',
        'cloud': '<path d="M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9Z"/>',
        'fog': '<path d="M4 14h16M4 18h16M6 10h12"/><path d="M8 6h8"/>',
        'rain': '<path d="M16 13V21M8 13v8M12 15v8"/><path d="M20 16.6A5 5 0 0 0 18 7h-1.3A8 8 0 1 0 4 15.3"/>',
        'snow': '<path d="M20 17.6A5 5 0 0 0 18 8h-1.3A8 8 0 1 0 4 16.3"/><path d="M8 15h.01M8 19h.01M12 17h.01M12 21h.01M16 15h.01M16 19h.01"/>',
        'storm': '<path d="M19 16.9A5 5 0 0 0 18 7h-1.3A8 8 0 1 0 4 15.3"/><path d="m13 11-4 6h6l-4 6"/>'
    };

    function weatherIcon(code) {
        var kind = (WEATHER[code] || ['', 'cloud'])[1];
        return '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' + ICONS[kind] + '</svg>';
    }

    function initWeather() {
        var widgets = $$('[data-weather]');
        var forecasts = $$('[data-forecast]');
        if (!widgets.length && !forecasts.length) return;
        var src = widgets[0] || forecasts[0];
        var lat = src.getAttribute('data-lat');
        var lon = src.getAttribute('data-lon');
        if (!lat || !lon) return;

        var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + lat + '&longitude=' + lon +
            '&current=temperature_2m,weather_code,wind_speed_10m' +
            '&daily=weather_code,temperature_2m_max,temperature_2m_min,snowfall_sum' +
            '&wind_speed_unit=ms&timezone=auto&forecast_days=7';

        fetch(url).then(function (r) { return r.ok ? r.json() : Promise.reject(); }).then(function (data) {
            widgets.forEach(function (w) {
                var c = data.current;
                var temp = Math.round(c.temperature_2m);
                $('[data-weather-temp]', w).textContent = (temp > 0 ? '+' : '') + temp + '°';
                var icon = $('[data-weather-icon]', w);
                if (icon) icon.innerHTML = weatherIcon(c.weather_code);
                var note = $('[data-weather-note]', w);
                if (note) note.textContent = (WEATHER[c.weather_code] || ['—'])[0] + ', ветер ' + Math.round(c.wind_speed_10m) + ' м/с';
                w.hidden = false;
            });

            forecasts.forEach(function (box) {
                var openDays = (box.getAttribute('data-open-days') || '').split(',').filter(Boolean).map(Number);
                var names = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
                var html = '';
                data.daily.time.forEach(function (day, i) {
                    var d = new Date(day + 'T12:00:00');
                    var pyWeekday = (d.getDay() + 6) % 7; // 0 = понедельник, как в Django
                    var isOpen = openDays.indexOf(pyWeekday) !== -1;
                    var max = Math.round(data.daily.temperature_2m_max[i]);
                    var min = Math.round(data.daily.temperature_2m_min[i]);
                    var snow = data.daily.snowfall_sum[i];
                    html += '<div class="forecast__day' + (isOpen ? ' is-open' : '') + '">' +
                        '<span class="forecast__name">' + (i === 0 ? 'сегодня' : names[d.getDay()]) + '</span>' +
                        '<span class="forecast__date">' + d.getDate() + '.' + String(d.getMonth() + 1).padStart(2, '0') + '</span>' +
                        '<span class="forecast__icon">' + weatherIcon(data.daily.weather_code[i]) + '</span>' +
                        '<span class="forecast__temp">' + max + '° <span>' + min + '°</span></span>' +
                        '<span class="forecast__snow">' + (snow > 0 ? '❄ ' + snow.toFixed(1).replace('.', ',') + ' см' : '') + '</span>' +
                        '</div>';
                });
                box.innerHTML = html;
            });
        }).catch(function () {
            forecasts.forEach(function (box) {
                box.innerHTML = '<p class="empty forecast__fallback">Прогноз временно недоступен.</p>';
            });
        });
    }

    /* ---------------------------------------------------------------------
       Плавная прокрутка (Lenis)
       --------------------------------------------------------------------- */
    function initSmoothScroll() {
        if (reduceMotion || typeof window.Lenis !== 'function') return;
        var lenis = new window.Lenis({
            duration: 1.15,
            easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
            smoothWheel: true,
            anchors: { offset: -110 },
        });
        window.__lenis = lenis;
        function raf(time) {
            lenis.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);
    }

    var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    var GLASS = '.feature, .pass, .card, .review, .route, .stats__item, .rental-item, .contact-card, .service-item';
    var TILT = '.feature, .pass, .card, .review, .route, .slope, .stats__item, .tile';

    /* ---------------------------------------------------------------------
       Свет за курсором внутри стекла
       --------------------------------------------------------------------- */
    function initGlare() {
        if (!finePointer) return;
        $$(GLASS).forEach(function (el) {
            el.addEventListener('pointermove', function (e) {
                var r = el.getBoundingClientRect();
                el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
                el.style.setProperty('--my', (e.clientY - r.top) + 'px');
            });
        });
        var light = document.createElement('div');
        light.className = 'cursor-light';
        document.body.appendChild(light);
        window.addEventListener('pointermove', function (e) {
            light.style.setProperty('--cx', e.clientX + 'px');
            light.style.setProperty('--cy', e.clientY + 'px');
        }, { passive: true });
    }

    /* ---------------------------------------------------------------------
       Лёгкий 3D-наклон карточек за курсором
       --------------------------------------------------------------------- */
    function initTilt() {
        if (!finePointer || reduceMotion) return;
        $$(TILT).forEach(function (el) {
            el.setAttribute('data-tilt', '');
            var max = el.classList.contains('tile') ? 7 : 5;
            el.addEventListener('pointermove', function (e) {
                var r = el.getBoundingClientRect();
                var x = (e.clientX - r.left) / r.width - 0.5;
                var y = (e.clientY - r.top) / r.height - 0.5;
                el.style.transition = 'transform .2s ease-out, border-color .4s, box-shadow .6s';
                el.style.transform = 'perspective(900px) rotateX(' + (-y * max).toFixed(2) + 'deg) rotateY(' +
                    (x * max).toFixed(2) + 'deg) translateY(-6px)';
            });
            el.addEventListener('pointerleave', function () {
                el.style.transition = 'transform .8s cubic-bezier(.16,1,.3,1), border-color .4s, box-shadow .6s';
                el.style.transform = '';
            });
        });
    }

    /* ---------------------------------------------------------------------
       «Магнитные» кнопки
       --------------------------------------------------------------------- */
    function initMagnetic() {
        if (!finePointer || reduceMotion) return;
        $$('.btn--primary, .btn--glass, .hero__arrow, .float-whatsapp').forEach(function (el) {
            el.addEventListener('pointermove', function (e) {
                var r = el.getBoundingClientRect();
                var x = e.clientX - r.left - r.width / 2;
                var y = e.clientY - r.top - r.height / 2;
                el.style.transform = 'translate(' + (x * 0.18).toFixed(1) + 'px,' + (y * 0.25).toFixed(1) + 'px)';
            });
            el.addEventListener('pointerleave', function () { el.style.transform = ''; });
        });
    }

    /* ---------------------------------------------------------------------
       Параллакс фона первого экрана
       --------------------------------------------------------------------- */
    function initParallax() {
        if (reduceMotion) return;
        var layers = $$('.hero__slides, .page-hero__bg');
        if (!layers.length) return;
        var ticking = false;
        function update() {
            var y = window.scrollY;
            layers.forEach(function (el) {
                el.style.transform = 'translate3d(0,' + (y * 0.35).toFixed(1) + 'px,0)';
            });
            ticking = false;
        }
        window.addEventListener('scroll', function () {
            if (!ticking) { requestAnimationFrame(update); ticking = true; }
        }, { passive: true });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initSmoothScroll();
        initHeader();
        initNav();
        initSlider();
        initReveal();
        initLightbox();
        initFilters();
        initScrollSpy();
        initForms();
        initMessages();
        initWeather();
        initGlare();
        initTilt();
        initMagnetic();
        initParallax();
    });
})();

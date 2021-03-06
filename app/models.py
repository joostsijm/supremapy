
"""
All models for module
"""

from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.sql.expression import false
from flask import url_for
from flask_login import UserMixin, current_user
import humanize
from app import db, argon2


class Game(db.Model):
    """Model for game"""

    __tablename__ = "sp_games"

    # Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer)
    game_host = db.Column(db.String)
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    end_of_game = db.Column(db.Boolean, server_default='f', default=False)
    day_of_game = db.Column(db.Integer)
    number_of_players = db.Column(db.Integer)
    password = db.Column(db.String)
    scenario = db.Column(db.Integer)
    ranked = db.Column(db.Integer)
    gold_round = db.Column(db.Boolean, server_default='f', default=False)
    ai_level = db.Column(db.Integer)
    country_selection = db.Column(db.Integer)
    time_scale = db.Column(db.DECIMAL(2, 1))
    team_setting = db.Column(db.Integer)
    team_victory_points = db.Column(db.Integer)
    victory_points = db.Column(db.Integer)
    research_days_offset = db.Column(db.Integer)
    research_time_scale = db.Column(db.DECIMAL(2, 1))
    next_day_time = db.Column(db.DateTime())

    track_game = db.Column(db.Boolean, server_default='f', default=False)
    track_players = db.Column(db.Boolean, server_default='f', default=False)
    track_score = db.Column(db.Boolean, server_default='f', default=False)
    track_relations = db.Column(db.Boolean, server_default='f', default=False)
    track_coalitions = db.Column(db.Boolean, server_default='f', default=False)
    track_market = db.Column(db.Boolean, server_default='f', default=False)

    # Relationships
    # -------------

    map_id = db.Column(db.Integer, db.ForeignKey("sp_maps.id"))
    map = db.relationship("Map", backref=db.backref("games"))

    # Attributes
    # -------------

    @hybrid_property
    def day(self):
        """Return current day of game"""
        delta = datetime.today() - self.start_at
        return delta.days + 2

    @hybrid_property
    def last_day(self):
        """Return last fetched day"""
        day = self.days.order_by(Day.day.desc()).first()
        if day is None:
            return 0
        return day.day

    @hybrid_property
    def url(self):
        """Return internal url"""
        return url_for("game_overview", game_id=self.game_id)

    @hybrid_property
    def supremacy_url(self):
        """Return supremacy website url"""
        url = "https://www.supremacy1914.com/play.php?gameID=%s" % str(self.game_id)
        if current_user.is_authenticated:
            player = self.players.filter(Player.user_id == current_user.id).first()
            if player is not None:
                return url + "&uid=" + str(current_user.site_id)
        return url + "&mode=guest"

    @hybrid_property
    def start_at_formatted(self):
        """Give natural start date"""
        return humanize.naturaldate(self.start_at)

    @hybrid_property
    def next_day_formatted(self):
        """Return natural date of next day"""
        if self.next_day_time > datetime.now():
            return humanize.naturaltime(self.next_day_time)
        return "unknown"

    @hybrid_property
    def active_players_count(self):
        """Count active non ai players"""
        return self.players.filter(
            Player.user_id.isnot(None)
        ).filter(Player.defeated == false()).count()

    @hybrid_method
    def active_players(self):
        """Return active non ai players"""
        return self.players.filter(
            Player.user_id.isnot(None)
        ).filter(Player.defeated == false()).all()

    @hybrid_method
    def all_players(self):
        """Return all non ai players"""
        return self.players.filter(
            Player.user_id.isnot(None)
        ).all()

    @hybrid_property
    def scenario_url(self):
        """Give image url for scenario"""
        return "https://supremacy1914.com/fileadmin/templates/supremacy_1914" + \
            "/images/scenarios/scenario_%s_small.jpg" % self.scenario

    # Representation
    # -------------

    def __repr__(self):
        return "<Game(%s)>" % (self.id)


class User(db.Model, UserMixin):
    """Model for User"""

    __tablename__ = "sp_users"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    site_id = db.Column(db.Integer, unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True)
    _password = db.Column("password", db.String(255))
    registration_at = db.Column(db.DateTime, default=datetime.utcnow)
    score_military = db.Column(db.Integer)
    score_economic = db.Column(db.Integer)

    # Attributes
    # -------------

    def __init__(self, id=None):
        self.id = id

    @hybrid_property
    def url(self):
        """Return url user profile"""
        return url_for("user_overview", site_id=self.site_id)

    @hybrid_property
    def supremacy_url(self):
        """Return url for supremacy user profile"""
        return "https://www.supremacy1914.com/index.php?id=59" + \
            "&tx_supgames_piUserPage[uid]=" + str(self.site_id)

    @property
    def password(self):
        """Return the password"""
        return self._password

    @password.setter
    def password(self, password):
        """Hash password"""
        self._password = argon2.generate_password_hash(password)

    def check_password(self, password):
        """Check if password is correct"""
        return argon2.check_password_hash(self.password, password)

    # Representation
    # -------------

    def __repr__(self):
        return "<User(%s)>" % (self.id)


class Player(db.Model):
    """Model for Player"""

    __tablename__ = "sp_players"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer)
    start_day = db.Column(db.Integer)

    title = db.Column(db.String, nullable=True)
    name = db.Column(db.String, nullable=False)
    nation_name = db.Column(db.String, nullable=False)

    primary_color = db.Column(db.String)
    secondary_color = db.Column(db.String)

    defeated = db.Column(db.Boolean, server_default='f', default=False)
    last_login = db.Column(db.DateTime)
    computer_player = db.Column(db.Boolean, server_default='f', default=False)
    native_computer = db.Column(db.Boolean, server_default='f', default=False)

    flag_image_id = db.Column(db.Integer)
    player_image_id = db.Column(db.Integer)

    # Relationships
    # -------------

    user_id = db.Column(db.Integer, db.ForeignKey("sp_users.id"))
    user = db.relationship("User", backref=db.backref("players", lazy="dynamic"))

    game_id = db.Column(db.Integer, db.ForeignKey("sp_games.id"))
    game = db.relationship("Game", backref=db.backref("players", lazy="dynamic"))

    # Attributes
    # -------------

    @hybrid_property
    def points(self):
        """Return the amount of points"""
        today = self.today()
        if today is not None:
            return today.points

        return 0

    @hybrid_method
    def today(self):
        """Return last day"""
        return self.days.order_by(Day.day.desc()).first()

    @hybrid_property
    def last_day_percentage(self):
        """Calculate percantage from last day"""
        today = self.today()
        if today is None:
            return 0

        yesterday = self.days.filter(Day.day == today.day - 1).first()
        if yesterday is None:
            return 0

        percentage = (today.points - yesterday.points) / yesterday.points * 100
        return round(percentage, 2)

    @hybrid_property
    def last_week_percentage(self):
        """Calculate percantage from last week"""
        today = self.today()
        if today is None:
            return 0

        last_week = self.days.filter(Day.day == today.day - 7).first()
        if last_week is None:
            return 0

        percentage = (today.points - last_week.points) / last_week.points * 100
        return round(percentage, 2)

    @hybrid_property
    def fullname(self):
        """Format fullname of player"""
        return "%s %s" % (self.title, self.name)

    @hybrid_property
    def last_login_formatted(self):
        """Format last login date"""
        if self.last_login is None:
            return ""

        return humanize.naturaltime(self.last_login)

    @hybrid_property
    def player_image_url(self):
        """Return url for player image"""
        if self.player_image_id != -1:
            return "https://static1.bytro.com/games/sup/%s/%s/%s.png" % (
                str(self.game.game_id)[:4],
                str(self.game.game_id)[-3:],
                self.player_image_id
            )
        return "https://www.supremacy1914.com/clients/s1914-client/" + \
            "s1914-client_live/images/map/avatars/%s/%s.jpg" % (
                self.game.map.map_id,
                self.player_id
            )


    @hybrid_property
    def flag_image_url(self):
        """Return url for flag image"""
        if self.player_image_id != -1:
            return "https://static1.bytro.com/games/sup/%s/%s/%s.png" % (
                str(self.game.game_id)[:4],
                str(self.game.game_id)[-3:],
                self.flag_image_id
            )
        return "https://www.supremacy1914.com/clients/s1914-client/" + \
            "s1914-client_live/images/map/flags/%s/small_%s.png" % (
                self.game.map.map_id,
                self.player_id
            )

    @hybrid_property
    def relations_sorted(self):
        """Return relations sorted"""
        return self.native_relations.order_by(Relation.status.desc()).all()

    # Representation
    # -------------

    def __repr__(self):
        return "<Player(%s)>" % (self.id)


class Relation(db.Model):
    """Model for Relations"""

    __tablename__ = "sp_relations"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    start_day = db.Column(db.Integer)
    end_day = db.Column(db.Integer)
    status = db.Column(db.Integer)

    # Relationships
    # -------------

    game_id = db.Column(db.Integer, db.ForeignKey("sp_games.id"))
    game = db.relationship("Game", backref=db.backref("relations", lazy="dynamic"))

    player_native_id = db.Column(db.Integer, db.ForeignKey("sp_players.id"))
    player_native = db.relationship("Player", foreign_keys="Relation.player_native_id", \
        backref=db.backref("native_relations", lazy="dynamic"))

    player_foreign_id = db.Column(db.Integer, db.ForeignKey("sp_players.id"))
    player_foreign = db.relationship("Player", foreign_keys="Relation.player_foreign_id", \
        backref=db.backref("foreign_relations", lazy="dynamic"))

    # Attributes
    # -------------

    @hybrid_property
    def status_formatted(self):
        """Return description of the relation"""
        status_list = {
            -2: "war",
            -1: "ceasefire",
            0: "trade-embargo",
            1: "peace",
            3: "right-of-way",
            4: "share-map",
            6: "share-info",
            7: "army-commmand"
        }

        status = self.status
        if status in status_list:
            return status_list[status]
        return "unknown"

    # Representation
    # -------------

    def __repr__(self):
        return "<Relation(%s)>" % (self.id)


class Day(db.Model):
    """Model for Day"""

    __tablename__ = "sp_days"

    # Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    points = db.Column(db.Integer)

    # Relationships
    # -------------

    player_id = db.Column(db.Integer, db.ForeignKey("sp_players.id"))
    player = db.relationship("Player", backref=db.backref("days", lazy="dynamic"))

    game_id = db.Column(db.Integer, db.ForeignKey("sp_games.id"))
    game = db.relationship("Game", backref=db.backref("days", lazy="dynamic"))

    coalition_id = db.Column(db.Integer, db.ForeignKey("sp_coalitions.id"))
    coalition = db.relationship("Coalition", backref=db.backref("days"))

    # Representation
    # -------------

    def __repr__(self):
        return "<Day(%s)>" % (self.id)


class Map(db.Model):
    """Model for a map"""

    __tablename__ = "sp_maps"

    # Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer)
    name = db.Column(db.String)
    image = db.Column(db.String)
    slots = db.Column(db.Integer)

    # Relationships
    # -------------

    # Representation
    # -------------

    def __repr__(self):
        return "<Map(%s)>" % (self.id)


class Coalition(db.Model):
    """Model for Coalition"""

    __tablename__ = "sp_coalitions"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    coaliton_id = db.Column(db.Integer)
    name = db.Column(db.String)
    description = db.Column(db.String)
    start_day = db.Column(db.Integer)
    end_day = db.Column(db.Integer)

    # Relationships
    # -------------

    game_id = db.Column(db.Integer, db.ForeignKey("sp_games.id"))
    game = db.relationship("Game", backref=db.backref("coalitions"))

    # Representation
    # -------------

    def __repr__(self):
        return "<Coalition(%s)>" % (self.id)


class Market(db.Model):
    """Model with information of current market"""

    __tablename__ = "sp_market"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # -------------

    game_id = db.Column(db.Integer, db.ForeignKey("sp_games.id"))
    game = db.relationship("Game", backref=db.backref("markets", lazy="dynamic"))

    # Attributes
    # -------------

    @hybrid_property
    def previous(self):
        """Return current day of game"""
        return self.game.markets.filter(Market.datetime < self.datetime) \
            .order_by(Market.datetime.desc()).first()

    @hybrid_property
    def price_list(self):
        """Return list of prices"""
        prices = {}
        for price in self.prices:
            prices[price.resource_id] = price
        return prices


    # Representation
    # -------------

    def __repr__(self):
        return "<Market(%s)>" % (self.id)

class Order(db.Model):
    """Model for Order"""

    __tablename__ = "sp_orders"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    limit = db.Column(db.DECIMAL(3, 1))
    buy = db.Column(db.Boolean, server_default='f', default=False)

    # Relationships
    # -------------

    market_id = db.Column(db.Integer, db.ForeignKey("sp_market.id"))
    market = db.relationship("Market", backref=db.backref("orders"))

    player_id = db.Column(db.Integer, db.ForeignKey("sp_players.id"))
    player = db.relationship("Player", backref=db.backref("orders"))

    resource_id = db.Column(db.Integer, db.ForeignKey("sp_resource.id"))
    resource = db.relationship("Resource", backref=db.backref("orders"))

    # Representation
    # -------------

    def __repr__(self):
        return "<Order(%s)>" % (self.id)

class Price(db.Model):
    """Model for Price"""

    __tablename__ = "sp_prices"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.DECIMAL(3, 1))
    buy = db.Column(db.Boolean, server_default='f', default=False)

    # Relationships
    # -------------

    market_id = db.Column(db.Integer, db.ForeignKey("sp_market.id"))
    market = db.relationship("Market", backref=db.backref("prices", lazy="dynamic"))

    resource_id = db.Column(db.Integer, db.ForeignKey("sp_resource.id"))
    resource = db.relationship("Resource", backref=db.backref("prices"))

    previous_id = db.Column(db.Integer, db.ForeignKey("sp_prices.id"))
    previous = db.relationship("Price", backref=db.backref("next"), uselist=False, remote_side=[id])

    # Representation
    # -------------

    def __repr__(self):
        return "<Price(%s)>" % (self.id)


class Resource(db.Model):
    """Model for Resource"""

    __tablename__ = "sp_resource"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    color = db.Column(db.String)

    # Representation
    # -------------

    def __repr__(self):
        return "<Resource(%s)>" % (self.id)


class SyncLog(db.Model):
    """Model to keep a log of sync"""

    __tablename__ = "sp_sync_log"

    # db.Columns
    # -------------

    id = db.Column(db.Integer, primary_key=True)
    function = db.Column(db.String)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    succes = db.Column(db.Boolean, server_default='f', default=False)

    # Relationships
    # -------------
    
    game_id = db.Column(db.Integer, db.ForeignKey("sp_games.id"))
    game = db.relationship("Game", backref=db.backref("sync_logs", lazy="dynamic"))

    # Representation
    # -------------

    def __repr__(self):
        return "<SyncLog(%s)>" % (self.id)
